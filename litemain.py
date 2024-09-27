import os
import concurrent.futures
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(filename="channel_processing.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# 读取频道名称模板
def load_channel_name_template(template_file):
    with open(template_file, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

# 解析M3U文件
def parse_m3u_file(m3u_file):
    with open(m3u_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    channels = []
    current_channel = {}
    
    for line in lines:
        if line.startswith("#EXTINF"):
            current_channel = {"info": line.strip()}
        elif line.startswith("http"):
            current_channel["url"] = line.strip()
            channels.append(current_channel)
            current_channel = {}
    
    return channels

# 使用ffprobe检查直播源的有效性
def check_stream(url):
    try:
        command = ['ffprobe', '-v', 'error', '-show_streams', '-i', url]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            # 可以提取更多的信息，比如分辨率等
            return True, result.stdout.decode('utf-8')
        else:
            return False, None
    except Exception as e:
        logging.error(f"Error checking stream {url}: {e}")
        return False, None

# 匹配频道名称与模板
def match_channel_name(channel_name, templates):
    for template_name in templates:
        if template_name in channel_name:
            return template_name
    return channel_name

# 处理频道列表
def process_channel(channel, templates):
    is_valid, stream_info = check_stream(channel["url"])
    if is_valid:
        channel_name = match_channel_name(channel["info"], templates)
        return {"name": channel_name, "url": channel["url"], "info": channel["info"]}
    else:
        logging.info(f"Invalid channel: {channel['url']}")
        return None

# 合并相似频道
def merge_channels(channels):
    merged = {}
    
    for channel in channels:
        if channel:
            name = channel["name"]
            if name in merged:
                merged[name]["urls"].append(channel["url"])
            else:
                merged[name] = {"info": channel["info"], "urls": [channel["url"]]}
    
    return merged

# 生成M3U文件
def generate_m3u(merged_channels, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("#EXTM3U\n")
        for name, data in merged_channels.items():
            file.write(f"{data['info']},{name}\n")
            for url in data["urls"]:
                file.write(f"{url}\n")

# 主函数，处理流程
def process_m3u_files(m3u_files, template_file, output_file):
    templates = load_channel_name_template(template_file)
    
    all_channels = []
    for m3u_file in m3u_files:
        all_channels.extend(parse_m3u_file(m3u_file))
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda channel: process_channel(channel, templates), all_channels))
    
    merged_channels = merge_channels(results)
    generate_m3u(merged_channels, output_file)

# 定时任务调用入口
if __name__ == "__main__":
    # 示例输入
    m3u_files = ["live.m3u"]  # 你的M3U文件列表
    template_file = "demo.txt"           # 你的频道模板文件
    output_file = "output_channels.m3u"              # 输出M3U文件

    process_m3u_files(m3u_files, template_file, output_file)
    logging.info("Channel processing complete.")

import re
import requests
import logging
from collections import defaultdict, OrderedDict
from datetime import datetime
import config
import asyncio
import aiohttp
import time

# 初始化日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("function.log", "w", encoding="utf-8"), logging.StreamHandler()])

# 解析模板文件，获取频道列表
def parse_template(template_file):
    template_channels = defaultdict(list)
    current_category = None

    with open(template_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                elif current_category:
                    channel_name = line.split(",")[0].strip()
                    template_channels[current_category].append(channel_name)

    return template_channels

# 获取网络链接中的频道
def fetch_channels(url):
    channels = defaultdict(list)
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        lines = response.text.split("\n")
        current_category = None
        is_m3u = any("#EXTINF" in line for line in lines[:15])
        logging.info(f"url: {url} 获取成功，判断为{'m3u' if is_m3u else 'txt'}格式")

        for line in lines:
            line = line.strip()
            if is_m3u:
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                elif line and not line.startswith("#"):
                    channel_url = line
                    if current_category and channel_name:
                        channels[current_category].append((channel_name, channel_url))
            else:
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                elif current_category:
                    match = re.match(r"^(.*?),(.*?)$", line)
                    if match:
                        channel_name = match.group(1).strip()
                        channel_url = match.group(2).strip()
                        channels[current_category].append((channel_name, channel_url))
                    elif line:
                        channels[current_category].append((line, ''))
                        
        logging.info(f"url: {url} 爬取成功✅，包含频道分类: {', '.join(channels.keys())}")

    except requests.RequestException as e:
        logging.error(f"url: {url} 爬取失败❌, Error: {e}")

    return channels

# 匹配模板中的频道与获取的网络频道
def match_channels(template_channels, all_channels):
    matched_channels = defaultdict(lambda: defaultdict(list))

    for category, channel_list in template_channels.items():
        for channel_name in channel_list:
            for online_category, online_channel_list in all_channels.items():
                for online_channel_name, online_channel_url in online_channel_list:
                    if channel_name == online_channel_name:
                        matched_channels[category][channel_name].append(online_channel_url)

    return matched_channels

# 根据模板文件和网络源获取匹配的频道
def filter_source_urls(template_file, source_urls):
    template_channels = parse_template(template_file)
    all_channels = defaultdict(list)
    for url in source_urls:
        fetched_channels = fetch_channels(url)
        for category, channel_list in fetched_channels.items():
            all_channels[category].extend(channel_list)

    matched_channels = match_channels(template_channels, all_channels)
    return matched_channels, template_channels

# 判断是否为IPv6地址
def is_ipv6(url):
    return re.match(r'^http:\/\/\[[0-9a-fA-F:]+\]', url) is not None

# 更新并写入结果文件
def updateChannelUrlsM3U(channels, template_channels, epg_urls, ip_version_priority, url_blacklist):
    written_urls = set()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("live.m3u", "w", encoding="utf-8") as f_m3u, open("live.txt", "w", encoding="utf-8") as f_txt:
        f_m3u.write(f"""#EXTM3U x-tvg-url={",".join(f'"{epg_url}"' for epg_url in epg_urls)}\n""")
        f_m3u.write(f"# 更新时间: {current_date}\n")

        for category, channel_list in template_channels.items():
            # 在分类下添加更新时间
            f_txt.write(f"{category},#genre#\n")
            f_txt.write(f"更新时间: {current_date}\n")
            
            if category in channels:
                for channel_name in channel_list:
                    if channel_name in channels[category]:
                        filtered_urls = [
                            url for url in sorted(channels[category][channel_name], key=lambda u: not is_ipv6(u) if ip_version_priority == "ipv6" else is_ipv6(u))
                            if url and url not in written_urls and not any(blacklist in url for blacklist in url_blacklist)
                        ]
                        
                        for url in filtered_urls:
                            written_urls.add(url)
                            new_url = f"{url}{'$IPV6' if is_ipv6(url) else '$IPV4'}"
                            f_m3u.write(f"#EXTINF:-1 tvg-id=\"{channel_name}\" tvg-name=\"{channel_name}\" tvg-logo=\"https://gitee.com/yuanzl77/TVBox-logo/raw/main/png/{channel_name}.png\" group-title=\"{category}\",{channel_name}\n")
                            f_m3u.write(new_url + "\n")
                            f_txt.write(f"{channel_name},{new_url}\n")

# 主执行逻辑
if __name__ == "__main__":
    template_file = "demo.txt"
    channels, template_channels = filter_source_urls(template_file)
    updateChannelUrlsM3U(channels, template_channels)

import re
import requests
import logging
from collections import defaultdict
from datetime import datetime
import asyncio
import aiohttp
import config

# 初始化日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("function.log", "w", encoding="utf-8"), logging.StreamHandler()])

def parse_template(template_file):
    """解析模板文件，获取频道列表"""
    template_channels = defaultdict(list)
    current_category = None

    with open(template_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#genre#" in line:
                current_category = line.split(",")[0].strip()
            elif current_category:
                template_channels[current_category].append(line.split(",")[0].strip())
    return template_channels

def fetch_channels(url):
    """从 URL 获取频道信息"""
    channels = defaultdict(list)
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        is_m3u = any("#EXTINF" in line for line in lines[:15])
        current_category, channel_name = None, None

        for line in lines:
            line = line.strip()
            if is_m3u:
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                elif line and not line.startswith("#"):
                    channels[current_category].append((channel_name, line))
            else:
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                elif current_category:
                    parts = line.split(",", 1)
                    channels[current_category].append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ''))

        logging.info(f"url: {url} 爬取成功✅，包含频道分类: {', '.join(channels.keys())}")
    except requests.RequestException as e:
        logging.error(f"url: {url} 爬取失败❌, Error: {e}")
    return channels

def match_channels(template_channels, all_channels):
    """匹配模板中的频道与获取的网络频道"""
    matched_channels = defaultdict(lambda: defaultdict(list))
    for category, channel_list in template_channels.items():
        for channel_name in channel_list:
            for online_category, online_channel_list in all_channels.items():
                matched_channels[category][channel_name].extend(
                    url for name, url in online_channel_list if channel_name == name)
    return matched_channels

async def check_connectivity(session, url):
    """检查 URL 连通性"""
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            return url
    except Exception as e:
        logging.error(f"连通性检查失败: {url} - {e}")
        return None

async def check_all_connectivities(urls):
    """异步检查所有 URL 的连通性"""
    async with aiohttp.ClientSession() as session:
        tasks = [check_connectivity(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [url for url in results if url]

def is_ipv6(url):
    """判断 URL 是否为 IPv6 地址"""
    return re.match(r'^http:\/\/\[[0-9a-fA-F:]+\]', url) is not None

def update_channel_urls_m3u(channels, template_channels, epg_urls, ip_version_priority, url_blacklist):
    """更新并写入结果文件"""
    written_urls = set()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("live.m3u", "w", encoding="utf-8") as f_m3u, open("live.txt", "w", encoding="utf-8") as f_txt:
        f_m3u.write(f"#EXTM3U x-tvg-url={','.join(f'\"{epg_url}\"' for epg_url in epg_urls)}\n")
        f_m3u.write(f"# 更新时间: {current_date}\n")

        for category, channel_list in template_channels.items():
            f_txt.write(f"{category},#genre#\n更新时间: {current_date}\n")
            if category in channels:
                for channel_name in channel_list:
                    if channel_name in channels[category]:
                        filtered_urls = [
                            url for url in sorted(channels[category][channel_name], key=lambda u: not is_ipv6(u) if ip_version_priority == "ipv6" else is_ipv6(u))
                            if url and url not in written_urls and not any(blacklist in url for blacklist in url_blacklist)
                        ]
                        ipv6_streams = [url for url in filtered_urls if is_ipv6(url)][:20]
                        ipv4_streams = [url for url in filtered_urls if not is_ipv6(url)][:20]
                        combined_streams = ipv6_streams + ipv4_streams

                        for index, url in enumerate(combined_streams, start=1):
                            url_suffix = f"$IPV6" if is_ipv6(url) else f"$IPV4"
                            base_url = url.split('$', 1)[0] if '$' in url else url
                            new_url = f"{base_url}{url_suffix}"

                            f_m3u.write(f"#EXTINF:-1 tvg-id=\"{index}\" tvg-name=\"{channel_name}\" "
                                        f"tvg-logo=\"https://gitee.com/yuanzl77/TVBox-logo/raw/main/png/{channel_name}.png\" "
                                        f"group-title=\"{category}\",{channel_name}\n{new_url}\n")
                            f_txt.write(f"{channel_name},{new_url}\n")

if __name__ == "__main__":
    from config import source_urls, epg_urls, ip_version_priority, url_blacklist, template_file

    # 使用正确的模板文件名
    template_file = "demo.txt"

    # 获取匹配的频道
    channels, template_channels = filter_source_urls(template_file, source_urls)
    
    # 更新并写入 M3U 和 TXT 文件
    update_channel_urls_m3u(channels, template_channels, epg_urls, ip_version_priority, url_blacklist)

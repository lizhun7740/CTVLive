import re
import requests
import logging
from collections import OrderedDict
from datetime import datetime
import config
import asyncio
import aiohttp
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("function.log", "w", encoding="utf-8"), 
    logging.StreamHandler()
])

def parse_template(template_file):
    """
    解析模板文件，提取频道类别及频道名称。
    """
    template_channels = OrderedDict()
    current_category = None

    with open(template_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    template_channels[current_category] = []
                elif current_category:
                    channel_name = line.split(",")[0].strip()
                    template_channels[current_category].append(channel_name)

    return template_channels

def fetch_channels(url):
    """
    从指定URL抓取频道数据，检测格式并解析。
    """
    channels = OrderedDict()
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        current_category = None
        is_m3u = any("#EXTINF" in line for line in lines[:15])
        source_type = "m3u" if is_m3u else "txt"
        logging.info(f"url: {url} 获取成功，检测为{source_type}格式")

        if is_m3u:
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                        channels.setdefault(current_category, []).append((channel_name, ''))
                elif line and not line.startswith("#"):
                    if current_category and channels[current_category]:
                        channels[current_category][-1] = (channels[current_category][-1][0], line.strip())
        else:
            for line in lines:
                line = line.strip()
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    channels[current_category] = []
                elif current_category:
                    match = re.match(r"^(.*?),(.*?)$", line)
                    if match:
                        channel_name = match.group(1).strip()
                        channel_url = match.group(2).strip()
                        channels[current_category].append((channel_name, channel_url))
                    elif line:
                        channels[current_category].append((line, ''))

    except requests.RequestException as e:
        logging.error(f"url: {url} 获取失败, 错误: {e}")

    return channels

def match_channels(template_channels, all_channels):
    """
    将抓取到的频道与模板中的频道进行匹配。
    """
    matched_channels = OrderedDict()

    for category, channel_list in template_channels.items():
        matched_channels[category] = OrderedDict()
        for channel_name in channel_list:
            for online_category, online_channel_list in all_channels.items():
                for online_channel_name, online_channel_url in online_channel_list:
                    if channel_name == online_channel_name:
                        matched_channels[category].setdefault(channel_name, []).append(online_channel_url)

    return matched_channels

async def ping_url(session, url):
    """
    异步检查URL的响应时间。
    """
    start_time = time.time()
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            return time.time() - start_time
    except Exception:
        return float('inf')

async def measure_streams_live_streams(live_streams):
    """
    异步测量直播流的响应时间。
    """
    async with aiohttp.ClientSession() as session:
        tasks = [ping_url(session, stream) for stream in live_streams]
        delays = await asyncio.gather(*tasks)
        return delays

def update_channel_urls_m3u(channels, template_channels):
    """
    更新M3U和TXT文件，包含选定的频道及更新时间。
    """
    written_urls = set()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("live.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write(f"#EXTM3U x-tvg-url={','.join(f'\"{epg_url}\"' for epg_url in config.epg_urls)}\n")

        with open("live.txt", "w", encoding="utf-8") as f_txt:
            f_txt.write(f"更新时间: {current_date}\n")
            f_m3u.write(f"# 更新时间: {current_date}\n")

            for category, channel_list in template_channels.items():
                f_txt.write(f"{category},#genre#\n")
                f_m3u.write(f"# {category}\n")
                if category in channels:
                    for channel_name in channel_list:
                        if channel_name in channels[category]:
                            urls = [url for url in channels[category][channel_name] if url[1] and url[1] not in written_urls and not any(blacklist in url[1] for blacklist in config.url_blacklist)]
                            written_urls.update(url[1] for url in urls)
                            sorted_urls = sorted(urls, key=lambda url: is_ipv6(url[1]))
                            ipv6_streams = [url for url in sorted_urls if is_ipv6(url[1])][:20]
                            ipv4_streams = [url for url in sorted_urls if not is_ipv6(url[1])][:20]

                            combined_streams = ipv6_streams + ipv4_streams
                            for index, (channel_name, url) in enumerate(combined_streams, start=1):
                                url_suffix = "$IPV6" if is_ipv6(url) else "$IPV4"
                                base_url = url.split('$', 1)[0] if '$' in url else url
                                new_url = f"{base_url}{url_suffix}"

                                f_m3u.write(f"#EXTINF:-1 tvg-id=\"{index}\" tvg-name=\"{channel_name}\" tvg-logo=\"https://gitee.com/yuanzl77/TVBox-logo/raw/main/png/{channel_name}.png\" group-title=\"{category}\",{channel_name}\n")
                                f_m3u.write(new_url + "\n")
                                f_txt.write(f"{channel_name},{new_url}\n")

            f_txt.write("\n")

if __name__ == "__main__":
    template_file = "demo.txt"
    channels, template_channels = filter_source_urls(template_file)
    asyncio.run(update_channel_urls_m3u(channels, template_channels))

import re
import requests
import logging
from collections import defaultdict
from datetime import datetime
import config

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("function.log", mode="w", encoding="utf-8"),
                              logging.StreamHandler()])

# 解析模板文件，获取频道分类及其对应的频道名称
def parse_template(template_file):
    with open(template_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    template_channels = defaultdict(list)
    current_category = None

    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            if "#genre#" in line:
                current_category = line.split(",")[0].strip()
            elif current_category:
                channel_name = line.split(",")[0].strip()
                template_channels[current_category].append(channel_name)

    return template_channels

# 从指定URL中获取频道及其直播源链接
def fetch_channels(url):
    channels = defaultdict(list)
    try:
        # 发送请求获取数据
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.splitlines()

        current_category = None
        is_m3u = any("#EXTINF" in line for line in lines[:15])
        logging.info(f"url: {url} 获取成功，判断为{'m3u' if is_m3u else 'txt'}格式")

        if is_m3u:
            # 解析m3u格式
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                elif line and not line.startswith("#") and current_category:
                    channel_url = line.strip()
                    channels[current_category].append((channel_name, channel_url))
        else:
            # 解析txt格式
            for line in lines:
                line = line.strip()
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                elif current_category:
                    match = re.match(r"^(.*?),(.*?)$", line)
                    if match:
                        channel_name = match.group(1).strip()
                        channel_url = match.group(2).strip()
                        channels[current_category].append((channel_name, channel_url))

        if channels:
            categories = ", ".join(channels.keys())
            logging.info(f"url: {url} 爬取成功✅，包含频道分类: {categories}")

    except requests.RequestException as e:
        logging.error(f"url: {url} 爬取失败❌, Error: {e}")

    return channels

# 读取blacklist.txt文件中的黑名单
def load_blacklist(blacklist_file):
    try:
        with open(blacklist_file, "r", encoding="utf-8") as f:
            blacklist = {line.strip() for line in f}
        logging.info(f"成功加载黑名单，包含 {len(blacklist)} 个URL")
    except FileNotFoundError:
        logging.warning(f"未找到 {blacklist_file} 文件，将创建新的黑名单")
        blacklist = set()
    return blacklist

# 根据模板文件中的频道列表过滤抓取到的频道，并剔除黑名单中的直播源
def match_channels(template_channels, all_channels, blacklist):
    matched_channels = defaultdict(lambda: defaultdict(list))
    for category, channel_list in template_channels.items():
        for channel_name in channel_list:
            for online_category, online_channel_list in all_channels.items():
                for online_channel_name, online_channel_url in online_channel_list:
                    if channel_name == online_channel_name and online_channel_url not in blacklist:
                        matched_channels[category][channel_name].append(online_channel_url)
    return matched_channels

# 从所有配置的源抓取频道并匹配模板中的频道
def filter_source_urls(template_file, blacklist_file):
    template_channels = parse_template(template_file)
    blacklist = load_blacklist(blacklist_file)
    all_channels = defaultdict(list)

    # 轮询所有源，抓取频道数据
    for url in config.source_urls:
        channels = fetch_channels(url)
        for category, channel_list in channels.items():
            all_channels[category].extend(channel_list)

    # 过滤频道并剔除黑名单中的直播源
    matched_channels = match_channels(template_channels, all_channels, blacklist)
    return matched_channels, template_channels

# 检查直播源的连通性
def check_connectivity(url, timeout=5):
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

# 判断URL是否为IPv6地址
def is_ipv6(url):
    try:
        return ":" in url.split('/')[2]
    except IndexError:
        return False

# 对URL进行IPv6和IPv4的整理
def sort_urls(urls):
    ipv6_streams = [url for url in urls if is_ipv6(url)][:20]
    ipv4_streams = [url for url in urls if not is_ipv6(url)][:20]
    combined_streams = ipv6_streams + ipv4_streams

    sorted_urls = []
    for index, url in enumerate(combined_streams, start=1):
        url_suffix = f"${'IPV6' if is_ipv6(url) else 'IPV4'}『线路{index}』" if len(combined_streams) > 1 else f"${'IPV6' if is_ipv6(url) else 'IPV4'}"
        base_url = url.split('$', 1)[0] if '$' in url else url
        sorted_urls.append(f"{base_url}{url_suffix}")
    return sorted_urls

# 更新黑名单，将无响应的URL写入blacklist.txt文件
def update_blacklist(blacklist_file, unresponsive_urls):
    with open(blacklist_file, "a", encoding="utf-8") as f:
        for url in unresponsive_urls:
            f.write(url + "\n")
    logging.info(f"已将 {len(unresponsive_urls)} 个无响应的URL添加到黑名单")

# 将匹配的频道写入M3U和TXT文件
def updateChannelUrlsM3U(channels, template_channels, blacklist_file):
    written_urls = set()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unresponsive_urls = set()

    with open("live.m3u", "w", encoding="utf-8") as f_m3u, open("live.txt", "w", encoding="utf-8") as f_txt:
        f_m3u.write(f"""#EXTM3U x-tvg-url={",".join(f'"{epg_url}"' for epg_url in config.epg_urls)}\n""")
        f_txt.write(f"更新时间,#genre#\n")
        f_txt.write(f"更新时间: {current_date}\n\n")
        f_m3u.write(f"# 更新时间: {current_date}\n\n")

        for category, channel_list in template_channels.items():
            f_txt.write(f"{category},#genre#\n")
            if category in channels:
                for channel_name in channel_list:
                    if channel_name in channels[category]:
                        # 检查和整理URL
                        valid_urls = [url for url in channels[category][channel_name] if check_connectivity(url)]
                        unresponsive_urls.update(url for url in channels[category][channel_name] if not check_connectivity(url))
                        combined_streams = sort_urls(valid_urls)

                        for index, url in enumerate(combined_streams, start=1):
                            if url not in written_urls:
                                written_urls.add(url)
                                f_m3u.write(f"#EXTINF:-1 tvg-id=\"{index}\" tvg-name=\"{channel_name}\" "
                                            f"tvg-logo=\"https://gitee.com/yuanzl77/TVBox-logo/raw/main/png/{channel_name}.png\" "
                                            f"group-title=\"{category}\",{channel_name}\n")
                                f_m3u.write(url + "\n")
                                f_txt.write(f"{channel_name},{url}\n")
            f_txt.write("\n")
        f_m3u.write("\n")

    # 更新黑名单
    update_blacklist(blacklist_file, unresponsive_urls)

# 主执行逻辑
if __name__ == "__main__":
    template_file = "demo.txt"
    blacklist_file = "blacklist.txt"
    channels, template_channels = filter_source_urls(template_file, blacklist_file)
    updateChannelUrlsM3U(channels, template_channels, blacklist_file)

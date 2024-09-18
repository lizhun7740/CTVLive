import re
import requests
import logging
from collections import defaultdict
from datetime import datetime
import config

# 配置日志记录
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.FileHandler("function.log", "w", encoding="utf-8"), 
                              logging.StreamHandler()])

# 解析模板文件，获取频道分类及其对应的频道列表
def parse_template(template_file):
    template_channels = defaultdict(list)  # 使用默认字典存储频道分类和频道列表
    current_category = None  # 当前分类

    with open(template_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()  # 去除行首尾空白
            if line and not line.startswith("#"):  # 忽略空行和注释行
                if "#genre#" in line:  # 如果包含分类标识
                    current_category = line.split(",")[0].strip()  # 获取当前分类名称
                elif current_category:  # 如果当前分类已定义
                    channel_name = line.split(",")[0].strip()  # 获取频道名称
                    template_channels[current_category].append(channel_name)  # 添加到对应分类下

    return template_channels

# 从指定URL中获取频道及其直播源链接
def fetch_channels(url):
    channels = defaultdict(list)  # 使用默认字典存储频道及其链接

    try:
        response = requests.get(url, timeout=10)  # 请求指定URL
        response.raise_for_status()  # 检查请求是否成功
        response.encoding = 'utf-8'  # 设置编码为UTF-8
        lines = response.text.splitlines()  # 按行分割响应文本

        current_category = None  # 当前分类
        is_m3u = any("#EXTINF" in line for line in lines[:15])  # 判断是否为M3U格式
        logging.info(f"url: {url} 获取成功，判断为{'m3u' if is_m3u else 'txt'}格式")

        if is_m3u:  # 如果是M3U格式
            for line in lines:
                line = line.strip()  # 去除行首尾空白
                if line.startswith("#EXTINF"):  # 处理频道信息行
                    match = re.search(r'group-title="(.*?)",(.*)', line)  # 正则匹配分类和频道名称
                    if match:
                        current_category = match.group(1).strip()  # 获取当前分类
                        channel_name = match.group(2).strip()  # 获取频道名称
                elif line and not line.startswith("#"):  # 忽略空行和注释行
                    channel_url = line.strip()  # 获取频道URL
                    if current_category and channel_name:  # 如果当前分类和频道名称已定义
                        channels[current_category].append((channel_name, channel_url))  # 添加频道及其链接
        else:  # 如果是TXT格式
            for line in lines:
                line = line.strip()  # 去除行首尾空白
                if "#genre#" in line:  # 如果包含分类标识
                    current_category = line.split(",")[0].strip()  # 获取当前分类名称
                elif current_category:  # 如果当前分类已定义
                    match = re.match(r"^(.*?),(.*?)$", line)  # 正则匹配频道名称和URL
                    if match:
                        channel_name = match.group(1).strip()  # 获取频道名称
                        channel_url = match.group(2).strip()  # 获取频道URL
                        channels[current_category].append((channel_name, channel_url))  # 添加到对应分类下
                    elif line:  # 如果行不为空
                        channels[current_category].append((line, ''))  # 添加频道名称，URL为空

        if channels:  # 如果成功获取到频道
            categories = ", ".join(channels.keys())  # 获取所有分类
            logging.info(f"url: {url} 爬取成功✅，包含频道分类: {categories}")
    except requests.RequestException as e:  # 捕获请求异常
        logging.error(f"url: {url} 爬取失败❌, Error: {e}")

    return channels  # 返回获取到的频道

# 根据模板文件中的频道列表过滤抓取到的频道
def match_channels(template_channels, all_channels):
    matched_channels = defaultdict(lambda: defaultdict(list))  # 存储匹配的频道

    for category, channel_list in template_channels.items():  # 遍历模板中的分类和频道
        for channel_name in channel_list:
            for online_category, online_channel_list in all_channels.items():  # 遍历抓取到的频道
                for online_channel_name, online_channel_url in online_channel_list:
                    if channel_name == online_channel_name:  # 如果频道名称匹配
                        matched_channels[category][channel_name].append(online_channel_url)  # 添加到匹配频道中

    return matched_channels  # 返回匹配的频道

# 从所有配置的源抓取频道并匹配模板中的频道
def filter_source_urls(template_file):
    template_channels = parse_template(template_file)  # 解析模板文件
    source_urls = config.source_urls  # 从配置中获取源URL

    all_channels = defaultdict(list)  # 存储所有抓取到的频道
    for url in source_urls:  # 遍历每个源URL
        fetched_channels = fetch_channels(url)  # 抓取频道
        for category, channel_list in fetched_channels.items():
            all_channels[category].extend(channel_list)  # 将抓取到的频道添加到总列表中

    matched_channels = match_channels(template_channels, all_channels)  # 匹配频道

    return matched_channels, template_channels  # 返回匹配的频道和模板频道

# 检查URL是否为IPv6
def is_ipv6(url):
    return re.match(r'^http:\/\/\[[0-9a-fA-F:]+\]', url) is not None  # 正则匹配IPv6格式

# 检查直播源的有效性
def is_stream_valid(url):
    try:
        response = requests.get(url, timeout=5)  # 设置较短的超时时间
        if response.status_code == 200:
            return True  # 如果状态码为200，认为直播源有效
    except requests.RequestException:
        pass
    return False  # 如果请求失败或状态码不是200，认为直播源无效

# 将匹配的频道写入M3U和TXT文件
def updateChannelUrlsM3U(channels, template_channels):
    written_urls = set()  # 存储已写入的URL，避免重复
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间

    # 写入M3U文件
    with open("live.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write(f"""#EXTM3U x-tvg-url={",".join(f'"{epg_url}"' for epg_url in config.epg_urls)}\n""")  # 写入EPG URL

        # 写入TXT文件
        with open("live.txt", "w", encoding="utf-8") as f_txt:
            # 添加更新时间分类
            f_txt.write(f"更新时间,#genre#\n")
            f_txt.write(f"更新时间: {current_date}\n\n")
            f_m3u.write(f"# 更新时间: {current_date}\n\n")

            for category, channel_list in template_channels.items():  # 遍历模板中的分类和频道
                f_txt.write(f"{category},#genre#\n")  # 写入分类到TXT
                if category in channels:  # 如果该分类在抓取的频道中
                    for channel_name in channel_list:
                        if channel_name in channels[category]:  # 如果频道名称匹配
                            # 根据配置优先级排序URL
                            sorted_urls = sorted(channels[category][channel_name], key=lambda url: not is_ipv6(url) if config.ip_version_priority == "ipv6" else is_ipv6(url))
                            # 过滤无效的直播源
                            valid_urls = [url for url in sorted_urls if url and url not in written_urls and is_stream_valid(url)]
                            written_urls.update(valid_urls)  # 更新已写入的URL集合

                            # 提取前20个IPv6和前20个IPv4的直播源
                            ipv6_streams = [url for url in valid_urls if is_ipv6(url)][:20]
                            ipv4_streams = [url for url in valid_urls if not is_ipv6(url)][:20]

                            # 将IPv6放在前面，IPv4放在后面
                            combined_streams = ipv6_streams + ipv4_streams

                            total_urls = len(combined_streams)  # 获取总URL数量
                            for index, url in enumerate(combined_streams, start=1):  # 遍历合并后的直播源
                                if is_ipv6(url):
                                    url_suffix = f"$IPV6" if total_urls == 1 else f"$IPV6『线路{index}』"
                                else:
                                    url_suffix = f"$IPV4" if total_urls == 1 else f"$IPV4『线路{index}』"
                                base_url = url.split(',')[0] if ',' in url else url  # 获取基础URL
                                new_url = f"{base_url}{url_suffix}"  # 生成新的URL

                                # 写入M3U文件
                                f_m3u.write(f"#EXTINF:-1 tvg-id=\"{index}\" tvg-name=\"{channel_name}\" tvg-logo=\"https://gitee.com/yuanzl77/TVBox-logo/raw/main/png/{channel_name}.png\" group-title=\"{category}\",{channel_name}\n")
                                f_m3u.write(new_url + "\n")  # 写入新的URL
                                f_txt.write(f"{channel_name},{new_url}\n")  # 写入TXT文件

            f_txt.write("\n")  # 写入换行

# 主执行逻辑
if __name__ == "__main__":
    template_file = "demo.txt"  # 模板文件名
    channels, template_channels = filter_source_urls(template_file)  # 过滤源URL并获取频道
    updateChannelUrlsM3U(channels, template_channels)  # 更新频道URL到M3U和TXT文件

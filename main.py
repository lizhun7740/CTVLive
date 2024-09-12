import requests  # 导入请求库，用于发送HTTP请求
import re  # 导入正则表达式库，用于字符串匹配
import socket  # 导入socket库，用于处理网络通信
import validators  # 导入validators库，用于验证URL的有效性
from concurrent.futures import ThreadPoolExecutor  # 导入线程池执行器，用于多线程处理
from datetime import datetime  # 导入datetime库，用于处理日期和时间

def fetch_data(url):
    "https://9295.kstore.space/ipv6.txt",
    "https://9295.kstore.space/ipv4.txt",
    "https://raw.githubusercontent.com/LuckyLearning/TV/master/local.txt",
    "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "https://gist.githubusercontent.com/inkss/0cf33e9f52fbb1f91bc5eb0144e504cf/raw/ipv6.m3u",
    "https://mirror.ghproxy.com/https://raw.githubusercontent.com/wwb521/live/main/tv.txt",
    "https://raw.githubusercontent.com/zhumeng11/IPTV/main/IPTV.m3u",
    "https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt",
    "https://raw.githubusercontent.com/n3rddd/CTVLive2/main/merged_output.m3u",
    "https://raw.githubusercontent.com/n3rddd/CTVLive2/main/others_output.txt",
    try:
        response = requests.get(url)  # 发送HTTP GET请求
        response.raise_for_status()  # 检查请求是否成功
        return response.text.splitlines()  # 返回响应内容的每一行
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")  # 捕获异常并打印错误信息
        return []

def parse_sources(file_content):
    """
    解析源文件内容，提取频道和URL信息。
    """
    sources = {}
    pattern = re.compile(r'#EXTINF:-1,(.+)\n(.+)')  # 匹配频道名和URL的正则表达式
    for i in range(len(file_content) - 1):
        match = pattern.match('\n'.join(file_content[i:i+2]))
        if match:
            channel, url = match.groups()
            if channel not in sources:
                sources[channel] = []
            sources[channel].append(url)
    return sources

def parse_blacklist(filename):
    """
    解析黑名单文件，返回有效的URL列表。
    """
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if validators.url(line.strip())]  # 验证URL并返回有效的URL列表
    except Exception as e:
        print(f"Error reading blacklist file {filename}: {e}")
        return []

def parse_dome(filename):
    """
    解析频道列表文件，返回频道名称列表。
    """
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f]  # 读取所有频道名称
    except Exception as e:
        print(f"Error reading dome file {filename}: {e}")
        return []

def remove_blacklisted(sources, blacklist):
    """
    从源列表中移除黑名单中的URL。
    """
    return {channel: [url for url in urls if url not in blacklist] for channel, urls in sources.items()}

def classify_sources_by_ip(sources):
    """
    按照IP类型（IPv4或IPv6）对源进行分类。
    """
    ipv4_sources = {}
    ipv6_sources = {}

    for channel, urls in sources.items():
        for url in urls:
            domain = re.findall(r'://(.*?)(?::|/|$)', url)  # 提取域名
            if domain:
                ip_type = classify_ip(domain[0])
                if ip_type == 'ipv4':
                    if channel not in ipv4_sources:
                        ipv4_sources[channel] = []
                    ipv4_sources[channel].append(url + ' #IPV4')
                elif ip_type == 'ipv6':
                    if channel not in ipv6_sources:
                        ipv6_sources[channel] = []
                    ipv6_sources[channel].append(url + ' #IPV6')
    return ipv4_sources, ipv6_sources

def classify_ip(domain):
    """
    根据域名判断IP类型（IPv4或IPv6）。
    """
    try:
        ip = socket.gethostbyname(domain)
        if ':' in ip:
            return 'ipv6'
        return 'ipv4'
    except socket.gaierror:
        return None

def extract_top_30(sources):
    """
    提取每个频道的前30个URL。
    """
    extracted = {}
    for channel, urls in sources.items():
        extracted[channel] = urls[:30]
    return extracted

def measure_latency(url):
    """
    测量指定URL的延迟。
    """
    try:
        start = datetime.now()
        requests.get(url, timeout=5)
        latency = (datetime.now() - start).total_seconds()
        return latency, url
    except requests.RequestException:
        return float('inf'), url

def test_latency(sources):
    """
    测试每个URL的延迟，并按延迟排序。
    """
    tested_sources = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for channel, urls in sources.items():
            latencies = list(executor.map(measure_latency, urls))
            valid_urls = [url for latency, url in sorted(latencies) if latency != float('inf')]
            if valid_urls:
                tested_sources[channel] = valid_urls
    return tested_sources

def write_to_live_file(filename, sources):
    """
    将测试结果写入文件。
    """
    try:
        with open(filename, 'w') as f:
            for channel, urls in sources.items():
                for url in urls:
                    f.write(f"{channel},{url}\n")
    except Exception as e:
        print(f"Error writing to file {filename}: {e}")

def main(urls, dome_file, blacklist_file):
    """
    主函数，处理所有逻辑。
    """
    all_sources = {}
    for url in urls:
        file_content = fetch_data(url)  # 获取数据
        sources = parse_sources(file_content)  # 解析数据
        for channel, urls in sources.items():
            if channel not in all_sources:
                all_sources[channel] = []
            all_sources[channel].extend(urls)

    dome_channels = parse_dome(dome_file)  # 解析频道列表文件
    all_sources = {channel: all_sources[channel] for channel in dome_channels if channel in all_sources}

    blacklist = parse_blacklist(blacklist_file)  # 解析黑名单文件
    whitelisted_sources = remove_blacklisted(all_sources, blacklist)  # 移除黑名单中的URL

    ipv4_sources, ipv6_sources = classify_sources_by_ip(whitelisted_sources)  # 按IP类型分类

    top_ipv4_sources = extract_top_30(ipv4_sources)  # 提取IPv4的前30个URL
    top_ipv6_sources = extract_top_30(ipv6_sources)  # 提取IPv6的前30个URL

    ipv4_tested = test_latency(top_ipv4_sources)  # 测试IPv4的延迟
    ipv6_tested = test_latency(top_ipv6_sources)  # 测试IPv6的延迟

    write_to_live_file('live_ipv4.txt', ipv4_tested)  # 写入IPv4结果
    write_to_live_file('live_ipv6.txt', ipv6_tested)  # 写入IPv6结果

if __name__ == "__main__":
    urls = ["http://example.com/source1.m3u", "http://example.com/source2.txt"]  # 这里添加你的URL
    main(urls, 'dome.txt', 'blacklist.txt')

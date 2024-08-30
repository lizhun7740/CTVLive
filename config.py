ip_version_priority = "ipv6"

source_urls = [
    "https://9295.kstore.space/ipv6.txt",
    "https://9295.kstore.space/ipv4.txt",
    "https://raw.githubusercontent.com/LuckyLearning/TV/master/local.txt",
    "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "https://gist.githubusercontent.com/inkss/0cf33e9f52fbb1f91bc5eb0144e504cf/raw/ipv6.m3u",
    "https://mirror.ghproxy.com/https://raw.githubusercontent.com/wwb521/live/main/tv.txt",
    "https://raw.githubusercontent.com/zhumeng11/IPTV/main/IPTV.m3u",
    "https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt",
]

url_blacklist = [

]

announcements = [
    {
        "channel": "定制直播",
        "entries": [
            {"name": "影视直播", "url": "https://cors.isteed.cc", "logo": "https://cors.isteed.cc"},
            {"name": "CrimeTV LIVE", "url": "https://cors.isteed.cc", "logo": "https://cors.isteed.cc"},
            {"name": "更新日期", "url": "https://cors.isteed.cc", "logo": "https://cors.isteed.cc"},
            {"name": None, "url": "https://cors.isteed.cc", "logo": "https://cors.isteed.cc"}
        ]
    }
]

epg_urls = [
    "https://live.fanmingming.com/e.xml",
    "http://epg.51zmt.top:8000/e.xml",
    "http://epg.aptvapp.com/xml",
    "https://epg.pw/xmltv/epg_CN.xml",
    "https://epg.pw/xmltv/epg_HK.xml",
    "https://epg.pw/xmltv/epg_TW.xml"
]

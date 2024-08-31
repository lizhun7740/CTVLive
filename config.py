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
    "https://raw.githubusercontent.com/n3rddd/CTVLive2/main/merged_output.m3u",
    "https://raw.githubusercontent.com/n3rddd/CTVLive2/main/others_output.txt",
    "http://175.178.251.183:6689/live.txt",
    "https://raw.githubusercontent.com/redrainl/iptv/main/speedtest/zubo_fofa.txt",  # ADDED BY LEM ON 01/08/2024
    "https://raw.githubusercontent.com/pxiptv/live/main/iptv.txt",  # ADDED BY LEM ON 08/08/2024
    "http://tv.850930.xyz/kdsb.m3u",  # ADDED BY LEM ON 29/07/2024
    "http://tv.850930.xyz/kdsb2.m3u",  # ADDED BY LEM ON 31/07/2024
    "http://tv.850930.xyz/gather.m3u",  # ADDED BY LEM ON 29/07/2024
    "https://raw.githubusercontent.com/hus888yu/app/main/111.m3u",  # ADDED BY LEM ON 06/08/2024
    "https://raw.githubusercontent.com/hus888yu/app/main/543.m3u",  # ADDED BY LEM ON 13/08/2024
    "http://175.178.251.183:6689/channel.txt",
    "http://120.79.4.185/new/mdlive.txt",
    "https://raw.githubusercontent.com/Fairy8o/IPTV/main/PDX-V4.txt",
    "https://raw.githubusercontent.com/Fairy8o/IPTV/main/PDX-V6.txt",
    "https://live.zhoujie218.top/tv/iptv6.txt",
    "https://tv.youdu.fan:666/live/",
    "http://ww.weidonglong.com/dsj.txt",
    "http://xhztv.top/zbc.txt",
    "https://raw.githubusercontent.com/mlvjfchen/TV/main/iptv_list.txt",
    "https://raw.githubusercontent.com/qingwen07/awesome-iptv/main/tvbox_live_all.txt",
    "https://v.nxog.top/m/tv/1/",
    "https://raw.githubusercontent.com/Guovin/TV/gd/result.txt",
    "http://home.jundie.top:81/Cat/tv/live.txt",
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv/hd.txt",
    "https://cdn.jsdelivr.net/gh/YueChan/live@main/IPTV.m3u",
    "https://raw.githubusercontent.com/cymz6/AutoIPTV-Hotel/main/lives.txt",
    "https://raw.githubusercontent.com/PizazzGY/TVBox_warehouse/main/live.txt",
    "https://fm1077.serv00.net/SmartTV.m3u",
    "https://raw.githubusercontent.com/ssili126/tv/main/itvlist.txt",
    "https://raw.githubusercontent.com/Supprise0901/TVBox_live/main/live.txt",  # ADDED BY LEM ON 29/07/2024
    "https://raw.githubusercontent.com/yoursmile66/TVBox/main/live.txt",  # ADDED BY LEM ON 29/07/2024
    "http://ttkx.live:55/lib/kx2024.txt",  # ADDED BY LEM ON 29/07/2024
    "https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u",  # ADDED BY LEM ON 29/07/2024
    "https://raw.githubusercontent.com/Love4vn/love4vn/main/Sport.m3u",  # 奥运 ON 29/07/2024
    "https://cdn.jsdelivr.net/gh/joevess/IPTV@main/sources/iptv_sources.m3u8",
    "https://cdn.jsdelivr.net/gh/joevess/IPTV@main/sources/home_sources.m3u8",
    "https://cdn.jsdelivr.net/gh/joevess/IPTV@main/iptv.m3u8",
    "https://cdn.jsdelivr.net/gh/ssili126/tv@main/itvlist.txt",
    "https://cdn.jsdelivr.net/gh/YueChan/Live@main/IPTV.m3u",
    "https://cdn.jsdelivr.net/gh/dxawi/0@main/tvlive.txt",
    "https://cdn.jsdelivr.net/gh/XiaoZhang5656/xiaozhang-5656.github.io@main/iptv-live.txt",
    "https://cdn.jsdelivr.net/gh/shidahuilang/shuyuan@shuyuan/iptv.txt",  # 这里也要确保是英文逗号
    "https://iptv.b2og.com/txt/q_bj_iptv_mobile.txt",
    "https://iptv.b2og.com/txt/cn_p.txt",
    "https://iptv.b2og.com/txt/o_cn.txt",
    "https://iptv.b2og.com/txt/q_bj_iptv_mobile_m.txt",
    "https://iptv.b2og.com/txt/m_iptv.txt",
    "https://iptv.b2og.com/txt/j_iptv.txt",
    "https://iptv.b2og.com/txt/j_home.txt",
    "https://iptv.b2og.com/txt/y_g.txt",
    "https://iptv.b2og.com/txt/ycl_iptv.txt",
    "https://iptv.b2og.com/txt/fmml_dv6.txt",
    "https://iptv.b2og.com/txt/fmml_ipv6.txt",
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

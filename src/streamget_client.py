# -*- encoding: utf-8 -*-

"""
統一透過 streamget 取得各平台直播源資訊，並轉換成主程式需要的 dict 格式。

streamget 由同作者維護（https://github.com/ihmily/streamget），
相較於內嵌在 src/spider.py 的解析代碼，能持續跟上平台變更。
"""
import dataclasses
import inspect

from streamget import (
    AcfunLiveStream,
    BaiduLiveStream,
    BigoLiveStream,
    BilibiliLiveStream,
    BluedLiveStream,
    ChangliaoLiveStream,
    ChzzkLiveStream,
    DouyuLiveStream,
    FaceitLiveStream,
    FlexTVLiveStream,
    HaixiuLiveStream,
    HuajiaoLiveStream,
    HuamaoLiveStream,
    HuyaLiveStream,
    InkeLiveStream,
    JDLiveStream,
    KwaiLiveStream,
    KugouLiveStream,
    LaixiuLiveStream,
    LangLiveStream,
    LehaiLiveStream,
    LianJieLiveStream,
    LiveMeLiveStream,
    LookLiveStream,
    MaoerLiveStream,
    NeteaseLiveStream,
    PandaLiveStream,
    PicartoLiveStream,
    PopkonTVLiveStream,
    RedNoteLiveStream,
    ShopeeLiveStream,
    ShowRoomLiveStream,
    SixRoomLiveStream,
    SoopLiveStream,
    TaobaoLiveStream,
    TikTokLiveStream,
    TwitCastingLiveStream,
    TwitchLiveStream,
    WeiboLiveStream,
    YiqiLiveStream,
    YoutubeLiveStream,
    YYLiveStream,
    ZhihuLiveStream,
)

# 平台名稱 -> (streamget 類別, 抓取方法: 'web' 或 'app')
# 方法選擇與 StreamCap 的 handlers.py 一致，為已驗證可行的呼叫方式
SG_PLATFORM_MAP = {
    'tiktok': (TikTokLiveStream, 'web'),
    'kuaishou': (KwaiLiveStream, 'web'),
    'huya': (HuyaLiveStream, 'app'),
    'douyu': (DouyuLiveStream, 'web'),
    'yy': (YYLiveStream, 'web'),
    'bilibili': (BilibiliLiveStream, 'web'),
    'xiaohongshu': (RedNoteLiveStream, 'app'),
    'bigo': (BigoLiveStream, 'web'),
    'blued': (BluedLiveStream, 'web'),
    'soop': (SoopLiveStream, 'web'),
    'netease': (NeteaseLiveStream, 'web'),
    'pandatv': (PandaLiveStream, 'web'),
    'maoerfm': (MaoerLiveStream, 'web'),
    'flextv': (FlexTVLiveStream, 'web'),
    'look': (LookLiveStream, 'web'),
    'popkontv': (PopkonTVLiveStream, 'web'),
    'twitcasting': (TwitCastingLiveStream, 'web'),
    'baidu': (BaiduLiveStream, 'web'),
    'weibo': (WeiboLiveStream, 'web'),
    'kugou': (KugouLiveStream, 'web'),
    'twitch': (TwitchLiveStream, 'web'),
    'liveme': (LiveMeLiveStream, 'web'),
    'huajiao': (HuajiaoLiveStream, 'app'),
    'showroom': (ShowRoomLiveStream, 'web'),
    'acfun': (AcfunLiveStream, 'web'),
    'changliao': (ChangliaoLiveStream, 'web'),
    'inke': (InkeLiveStream, 'web'),
    'zhihu': (ZhihuLiveStream, 'web'),
    'chzzk': (ChzzkLiveStream, 'web'),
    'haixiu': (HaixiuLiveStream, 'web'),
    '17live': (YiqiLiveStream, 'web'),
    'langlive': (LangLiveStream, 'web'),
    'sixroom': (SixRoomLiveStream, 'web'),
    'lehai': (LehaiLiveStream, 'web'),
    'huamao': (HuamaoLiveStream, 'web'),
    'shopee': (ShopeeLiveStream, 'app'),
    'youtube': (YoutubeLiveStream, 'web'),
    'taobao': (TaobaoLiveStream, 'web'),
    'jd': (JDLiveStream, 'web'),
    'faceit': (FaceitLiveStream, 'web'),
    'lianjie': (LianJieLiveStream, 'web'),
    'laixiu': (LaixiuLiveStream, 'web'),
    'picarto': (PicartoLiveStream, 'web'),
}


async def fetch_stream_info(platform_key: str, live_url: str, proxy_addr: str | None = None,
                            cookies: str | None = None, record_quality: str | None = 'OD',
                            **extra) -> dict:
    """
    透過 streamget 取得平台直播源資訊，回傳與主程式 port_info 相容的 dict。

    Args:
        platform_key: SG_PLATFORM_MAP 中的平台名稱。
        live_url: 直播間網址。
        proxy_addr: 代理位址。
        cookies: Cookie。
        record_quality: 畫質代碼（OD/UHD/HD/SD/LD）。
        **extra: 各平台額外參數（如 username/password/access_token/partner_code/account_type）。
    """
    if platform_key not in SG_PLATFORM_MAP:
        raise ValueError(f"平台 {platform_key} 尚未遷移到 streamget")
    stream_class, method = SG_PLATFORM_MAP[platform_key]

    init_params = inspect.signature(stream_class.__init__).parameters
    kwargs = {'proxy_addr': proxy_addr, 'cookies': cookies}
    kwargs.update(extra)
    kwargs = {key: value for key, value in kwargs.items() if key in init_params}
    live_stream = stream_class(**kwargs)

    if method == 'app':
        json_data = await live_stream.fetch_app_stream_data(url=live_url)
    else:
        json_data = await live_stream.fetch_web_stream_data(url=live_url)
    stream_data = await live_stream.fetch_stream_url(json_data, record_quality)
    return dataclasses.asdict(stream_data)
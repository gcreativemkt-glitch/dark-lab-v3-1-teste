"""Amostra FICTÍCIA para explorar a interface sem qualquer credencial."""
from datetime import datetime, timedelta, timezone
from analytics import channel_metrics

NOW = datetime.now(timezone.utc)
CHANNELS = [
    ('demo1','Midnight Room Sessions',120,38000,7800000,37),
    ('demo2','LoFi Rain Library',240,14500,3400000,42),
    ('demo3','Forgotten Castle Audio',80,7200,1100000,18),
    ('demo4','Soft Jazz Evenings',440,95000,22500000,118),
    ('demo5','Calm Focus Frequencies',65,4100,410000,14),
    ('demo6','Noir Blues Station',190,25000,5900000,51),
]


def demo_channels(query=''):
    result = []
    for cid, title, days, subs, views, count in CHANNELS:
        entry = dict(channel_id=cid,title=title,published_at=(NOW-timedelta(days=days)).isoformat(),
            subscribers=subs,views=views,video_count=count,thumbnail='',
            url='',sample_video_title=f'{title} | Mix de referência (simulação)',
            sample_video_views=int(views*.23),description='Canal inteiramente fictício. Dados de demonstração.')
        result.append(channel_metrics(entry))
    return result


def demo_videos(channel_id='demo1'):
    channel = next((c for c in demo_channels() if c['channel_id']==channel_id),demo_channels()[0])
    factors = [1.1,.7,.8,3.9,.6,1.2,.95,5.8,.5,1.05,.75,1.9,.62,1.4,1.05,0.8]
    return [dict(video_id=f'demo-{i}',title=f'{channel["title"]} • sessão {i+1} • chuva e atmosfera',
        channel_id=channel['channel_id'],channel_title=channel['title'],
        published_at=(NOW-timedelta(days=7+(len(factors)-i)*5)).isoformat(),
        views=int(15500*mult),likes=900,comments=40,thumbnail='',url='')
        for i,mult in enumerate(factors)]

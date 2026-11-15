"""Cliente da API oficial do YouTube; sem scraping ou bibliotecas pesadas."""
from __future__ import annotations
from urllib.parse import urlparse
import requests
import streamlit as st
from analytics import integer

BASE = 'https://www.googleapis.com/youtube/v3/'


class YouTubeError(RuntimeError):
    pass


@st.cache_data(ttl=1800, max_entries=256, show_spinner=False)
def _api_call(endpoint: str, args: tuple, key: str):
    try:
        response = requests.get(BASE + endpoint, params={**dict(args), 'key': key}, timeout=22)
        payload = response.json()
        if not response.ok:
            err = payload.get('error', {})
            raise YouTubeError(f"Erro do YouTube ({response.status_code}): {err.get('message', 'Falha na consulta')}.")
        return payload
    except requests.RequestException as ex:
        raise YouTubeError(f'Falha de conexão com o YouTube: {ex}') from ex
    except ValueError as ex:
        raise YouTubeError('O YouTube respondeu com dados inesperados.') from ex


def call(endpoint, key, **kwargs):
    if not key:
        raise YouTubeError('Configure YOUTUBE_API_KEY para usar consultas reais.')
    return _api_call(endpoint, tuple(sorted(kwargs.items())), key)


def get_channels(channel_ids, key):
    unique_ids = list(dict.fromkeys(cid for cid in channel_ids if cid))
    results = []
    for start in range(0, len(unique_ids), 50):
        res = call('channels', key, part='snippet,statistics,contentDetails', id=','.join(unique_ids[start:start+50]), maxResults=50)
        results += [normalize_channel(c) for c in res.get('items', [])]
    return results


def normalize_channel(c):
    sn = c.get('snippet', {})
    stats = c.get('statistics', {})
    return {
        'channel_id': c.get('id', ''),
        'title': sn.get('title', 'Sem título'),
        'description': sn.get('description', ''),
        'published_at': sn.get('publishedAt', ''),
        'thumbnail': sn.get('thumbnails', {}).get('medium', {}).get('url', ''),
        'subscribers': None if stats.get('hiddenSubscriberCount') else integer(stats.get('subscriberCount')),
        'views': integer(stats.get('viewCount')),
        'video_count': integer(stats.get('videoCount')),
        'uploads_playlist': c.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads', ''),
        'url': f"https://www.youtube.com/channel/{c.get('id','')}",
    }


def normalize_video(v):
    sn = v.get('snippet', {})
    stats = v.get('statistics', {})
    vid = v.get('id', '')
    return {
        'video_id': vid,
        'title': sn.get('title', 'Sem título'),
        'channel_id': sn.get('channelId', ''),
        'channel_title': sn.get('channelTitle', ''),
        'published_at': sn.get('publishedAt', ''),
        'views': integer(stats.get('viewCount')),
        'likes': integer(stats.get('likeCount')),
        'comments': integer(stats.get('commentCount')),
        'thumbnail': sn.get('thumbnails', {}).get('medium', {}).get('url', ''),
        'url': f'https://www.youtube.com/watch?v={vid}',
    }


def get_videos(video_ids, key):
    ids = list(dict.fromkeys(vid for vid in video_ids if vid))
    all_videos = []
    for pos in range(0, len(ids), 50):
        res = call('videos', key, part='snippet,statistics,contentDetails', id=','.join(ids[pos:pos+50]), maxResults=50)
        all_videos += [normalize_video(v) for v in res.get('items', [])]
    return all_videos


def search_videos(query, key, order='viewCount', limit=40, published_after=None):
    args = {'part':'snippet','q':query,'type':'video','order':order,'maxResults':max(1,min(limit,50))}
    if published_after:
        args['publishedAfter'] = published_after
    found = call('search', key, **args).get('items', [])
    ids = [v.get('id',{}).get('videoId') for v in found]
    indexed = {v['video_id']:v for v in get_videos(ids,key)}
    return [indexed[vid] for vid in ids if vid in indexed]


def discover_channels(query, key, order='viewCount', limit=40, published_after=None):
    videos = search_videos(query,key,order,limit,published_after)
    ids = list(dict.fromkeys(v['channel_id'] for v in videos if v.get('channel_id')))
    channels = get_channels(ids,key)
    best = {}
    for v in videos:
        cid = v['channel_id']
        if cid not in best or v['views'] > best[cid]['views']:
            best[cid] = v
    for c in channels:
        top = best.get(c['channel_id'], {})
        c['sample_video_title'] = top.get('title','')
        c['sample_video_views'] = top.get('views',0)
    return channels, videos


def get_channel(ref, key):
    ref = ref.strip()
    path = urlparse(ref).path.strip('/') if ref.startswith(('http://','https://')) else ref
    if path.startswith('channel/'):
        path = path.split('/', 1)[1]
    if path.startswith('@'):
        payload = call('channels', key, part='snippet,statistics,contentDetails', forHandle=path)
    elif path.startswith('UC') and len(path) == 24:
        payload = call('channels', key, part='snippet,statistics,contentDetails', id=path)
    else:
        raise YouTubeError('Cole um link /channel/UC..., um link /@usuario ou @usuario. Links /c/ e nomes soltos não são suportados nesta versão.')
    items = payload.get('items', [])
    if not items:
        raise YouTubeError('Canal não encontrado. Verifique o endereço.')
    return normalize_channel(items[0])


def latest_channel_videos(channel, key, limit=50):
    playlist = channel.get('uploads_playlist')
    if not playlist:
        raise YouTubeError('Este canal não disponibiliza a playlist de uploads.')
    found = call('playlistItems', key, part='contentDetails', playlistId=playlist, maxResults=max(1, min(limit,50))).get('items', [])
    ids = [item.get('contentDetails',{}).get('videoId') for item in found]
    indexed = {v['video_id']: v for v in get_videos(ids,key)}
    return [indexed[vid] for vid in ids if vid in indexed]


def scan_niche_two_views(query, key, published_after=None, each_limit=25):
    """Amostra de dois ordenamentos distintos: popularidade e publicação recente.

    Não realiza busca exaustiva no YouTube; limita cotas por clique.
    """
    popular = search_videos(query, key, 'viewCount', each_limit, published_after)
    fresh = search_videos(query, key, 'date', each_limit, published_after)
    deduped = {v['video_id']: v for v in popular + fresh if v.get('video_id')}
    videos = list(deduped.values())
    channel_ids = list(dict.fromkeys(v.get('channel_id') for v in videos if v.get('channel_id')))
    channels = get_channels(channel_ids, key)
    return channels, videos

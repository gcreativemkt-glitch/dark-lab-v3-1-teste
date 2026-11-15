"""Persistência SQLite local ou Supabase PostgREST (opcional)."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
import sqlite3
import requests

LOCAL_DB = Path(__file__).parent / 'data' / 'darklab.db'


class Store:
    def __init__(self, url='', key=''):
        self.url = url.strip().rstrip('/')
        self.key = key.strip()
        self.remote = bool(self.url and self.key)
        if not self.remote:
            LOCAL_DB.parent.mkdir(exist_ok=True)
            with self._connect() as conn:
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS watchlist (
                      channel_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                      note TEXT DEFAULT '', created_at TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS projects (
                      id TEXT PRIMARY KEY, name TEXT NOT NULL, niche TEXT DEFAULT '',
                      status TEXT DEFAULT 'Ideia', notes TEXT DEFAULT '', created_at TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS channel_snapshots (
                      channel_id TEXT NOT NULL, recorded_on TEXT NOT NULL,
                      subscribers INTEGER, views INTEGER, video_count INTEGER,
                      PRIMARY KEY(channel_id,recorded_on));
                    CREATE TABLE IF NOT EXISTS video_snapshots (
                      video_id TEXT NOT NULL, recorded_on TEXT NOT NULL,
                      views INTEGER NOT NULL, PRIMARY KEY(video_id, recorded_on));
                ''')

    def _connect(self):
        return sqlite3.connect(LOCAL_DB, timeout=8)

    def _remote(self, table, method='GET', params=None, json=None):
        if table not in ('watchlist','projects','channel_snapshots','video_snapshots'):
            raise ValueError('Tabela não permitida')
        response = requests.request(method, f'{self.url}/rest/v1/{table}', params=params,
            json=json, timeout=15, headers={
                'apikey':self.key, 'Authorization':f'Bearer {self.key}',
                'Content-Type':'application/json', 'Prefer':'resolution=merge-duplicates,return=minimal'
            })
        if not response.ok:
            raise RuntimeError(f'Falha ao acessar banco remoto: HTTP {response.status_code}. Verifique tabelas e credenciais.')
        return response.json() if response.content else []

    def watchlist(self):
        if self.remote:
            return self._remote('watchlist', params={'select':'*','order':'created_at.desc'})
        with self._connect() as c:
            c.row_factory = sqlite3.Row
            return [dict(x) for x in c.execute('SELECT * FROM watchlist ORDER BY created_at DESC')]

    def add_watch(self, channel_id, title, note=''):
        data = {'channel_id':channel_id,'title':title,'note':note,
                'created_at':datetime.now(timezone.utc).isoformat()}
        if self.remote:
            self._remote('watchlist', method='POST', json=data)
        else:
            with self._connect() as c:
                c.execute('INSERT INTO watchlist VALUES(:channel_id,:title,:note,:created_at) '
                          'ON CONFLICT(channel_id) DO UPDATE SET title=excluded.title,note=excluded.note',data)

    def remove_watch(self, channel_id):
        if self.remote:
            self._remote('watchlist', method='DELETE', params={'channel_id':f'eq.{channel_id}'})
        else:
            with self._connect() as c:
                c.execute('DELETE FROM watchlist WHERE channel_id=?',(channel_id,))

    def projects(self):
        if self.remote:
            return self._remote('projects', params={'select':'*','order':'created_at.desc'})
        with self._connect() as c:
            c.row_factory = sqlite3.Row
            return [dict(x) for x in c.execute('SELECT * FROM projects ORDER BY created_at DESC')]

    def add_project(self, name, niche, status, notes):
        data = {'id':str(uuid4()), 'name':name, 'niche':niche, 'status':status, 'notes':notes,
                'created_at':datetime.now(timezone.utc).isoformat()}
        if self.remote:
            self._remote('projects',method='POST',json=data)
        else:
            with self._connect() as c:
                c.execute('INSERT INTO projects VALUES(:id,:name,:niche,:status,:notes,:created_at)',data)

    def remove_project(self, pid):
        if self.remote:
            self._remote('projects',method='DELETE',params={'id':f'eq.{pid}'})
        else:
            with self._connect() as c:
                c.execute('DELETE FROM projects WHERE id=?',(pid,))

    def save_snapshot(self, channel):
        data = {'channel_id': channel['channel_id'],
                'recorded_on':datetime.now(timezone.utc).date().isoformat(),
                'subscribers':channel.get('subscribers'), 'views':channel.get('views'),
                'video_count':channel.get('video_count')}
        if self.remote:
            self._remote('channel_snapshots',method='POST',json=data)
        else:
            with self._connect() as c:
                c.execute('''INSERT INTO channel_snapshots VALUES
                          (:channel_id,:recorded_on,:subscribers,:views,:video_count)
                          ON CONFLICT(channel_id,recorded_on) DO UPDATE SET
                          subscribers=excluded.subscribers,views=excluded.views,video_count=excluded.video_count''',data)

    def snapshots(self, channel_id):
        if self.remote:
            return self._remote('channel_snapshots',params={
                'select':'*','channel_id':f'eq.{channel_id}','order':'recorded_on.asc'})
        with self._connect() as c:
            c.row_factory = sqlite3.Row
            return [dict(x) for x in c.execute(
                'SELECT * FROM channel_snapshots WHERE channel_id=? ORDER BY recorded_on',(channel_id,))]

    def observed_video_growth(self, videos):
        """Retorna crescimento diário observado para vídeos com coleta de dia anterior."""
        from datetime import date
        ids = list(dict.fromkeys(v.get('video_id') for v in videos if v.get('video_id')))
        if not ids:
            return {}
        historical = []
        if self.remote:
            for start in range(0, len(ids), 40):
                subset = ids[start:start + 40]
                historical.extend(self._remote('video_snapshots', params={
                    'select': 'video_id,recorded_on,views',
                    'video_id': 'in.(' + ','.join(subset) + ')',
                    'order': 'recorded_on.desc',
                }))
        else:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                for start in range(0, len(ids), 500):
                    subset = ids[start:start + 500]
                    marks = ','.join('?' for _ in subset)
                    historical.extend(dict(x) for x in conn.execute(
                        f'SELECT video_id,recorded_on,views FROM video_snapshots WHERE video_id IN ({marks}) ORDER BY recorded_on DESC',
                        subset))
        by_id = {}
        for row in historical:
            by_id.setdefault(row['video_id'], []).append(row)
        today = datetime.now(timezone.utc).date()
        growth = {}
        for video in videos:
            vid = video.get('video_id')
            if not vid:
                continue
            for old in by_id.get(vid, []):
                days = (today - date.fromisoformat(str(old['recorded_on'])[:10])).days
                if days >= 1:
                    growth[vid] = max(0, (int(video.get('views') or 0) - int(old['views'])) / days)
                    break
        return growth

    def save_video_snapshots(self, videos):
        """Grava uma observação por vídeo/dia; nunca inventa crescimento histórico."""
        day = datetime.now(timezone.utc).date().isoformat()
        rows = [
            {'video_id': v['video_id'], 'recorded_on': day, 'views': max(0, int(v.get('views') or 0))}
            for v in videos if v.get('video_id')
        ]
        rows = list({r['video_id']: r for r in rows}.values())
        if not rows:
            return
        if self.remote:
            for start in range(0, len(rows), 100):
                self._remote('video_snapshots', method='POST', json=rows[start:start + 100])
        else:
            with self._connect() as conn:
                conn.executemany('''INSERT INTO video_snapshots(video_id,recorded_on,views)
                    VALUES(:video_id,:recorded_on,:views)
                    ON CONFLICT(video_id,recorded_on) DO UPDATE SET views=excluded.views''', rows)

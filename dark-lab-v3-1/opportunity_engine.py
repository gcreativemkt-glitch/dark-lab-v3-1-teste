"""Avaliação conservadora de oportunidades a partir de amostras públicas do YouTube.

Nenhuma métrica aqui revela demanda de busca, RPM, monetização ou concorrência
TOTAL do YouTube. Scores são índices exploratórios, não probabilidades.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import log1p
from statistics import median
from analytics import age_days, integer, detect_preset, title_keywords


def _clip(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def evaluate_opportunity(query, videos, channels=None, observed_growth=None, methods=1):
    """Mede tração, espaço para canais novos e concentração NA AMOSTRA."""
    videos = [v for v in (videos or []) if v.get('video_id') and v.get('channel_id')]
    channel_map = {c['channel_id']: c for c in (channels or []) if c.get('channel_id')}
    observed_growth = observed_growth or {}
    n = len(videos)
    unique = len({v['channel_id'] for v in videos})
    today = datetime.now(timezone.utc)
    recent = [v for v in videos if (age_days(v.get('published_at'), today) or 100000) <= 90]
    vpd = [integer(v.get('views')) / max(1, age_days(v.get('published_at'), today) or 1) for v in recent]
    median_vpd = round(median(vpd)) if vpd else 0
    young_ids = {
        c['channel_id'] for c in channel_map.values()
        if 0 < (age_days(c.get('published_at'), today) or 0) <= 365
    }
    young_recent = [v for v in recent if v['channel_id'] in young_ids]
    breakout_ids = {
        v['channel_id'] for v in young_recent
        if integer(v.get('views')) >= 10000 and
           integer(v.get('views')) / max(1, age_days(v.get('published_at'), today) or 1) >= 250
    }

    views_by_channel = defaultdict(int)
    for v in videos:
        views_by_channel[v['channel_id']] += max(0, integer(v.get('views')))
    total_views = sum(views_by_channel.values())
    top3_share = (sum(sorted(views_by_channel.values(), reverse=True)[:3]) / total_views) if total_views else 1.0
    young_share = len(breakout_ids) / max(1, unique)
    recent_share = len(recent) / max(1, n)
    growth_values = [float(x) for x in observed_growth.values() if x is not None and x >= 0]
    median_growth = round(median(growth_values)) if growth_values else None

    # Heurística explícita: favorece tração, novos canais e menor concentração
    # na amostra; não estima "concorrentes totais" nem "saturação real".
    traction = _clip(log1p(median_vpd) / log1p(5000))
    newcomers = _clip(len(breakout_ids) / 4)
    dispersion = 1.0 - top3_share
    recency = _clip(recent_share / 0.75)
    confidence_points = (n >= 20) + (unique >= 8) + (len(recent) >= 12) + (methods >= 2) + (len(channel_map) >= 5)
    confidence = ('Baixa' if confidence_points <= 2 else 'Moderada' if confidence_points <= 4 else 'Boa para triagem')
    evidence_ok = n >= 12 and unique >= 5 and len(recent) >= 8 and bool(channel_map)
    raw_score = round(100 * (0.35 * traction + 0.30 * newcomers + 0.20 * dispersion + 0.15 * recency))
    score = min(raw_score, 49) if not evidence_ok else raw_score

    if not evidence_ok:
        status = 'Dados insuficientes'
    elif len(breakout_ids) >= 3 and median_vpd >= 250 and top3_share <= 0.72:
        status = 'Sinais de abertura (na amostra)'
    elif len(breakout_ids) >= 1 and median_vpd >= 100:
        status = 'Oportunidade a investigar'
    else:
        status = 'Sem evidência suficiente de entrada fácil'

    notes = []
    if n < 20 or unique < 8:
        notes.append('Amostra pequena: repetir com mais termos de busca e canais')
    if len(breakout_ids) < 3:
        notes.append('Poucos canais jovens com vídeos expressivos na amostra')
    if top3_share > 0.72:
        notes.append('Visualizações concentradas em até três canais da amostra')
    if median_growth is None:
        notes.append('Crescimento real ainda não observado: atualizar a pesquisa em outro dia')
    if not notes:
        notes.append('Sinais positivos na amostra; validar conteúdo e monetização antes de produzir em escala')

    top_candidates = sorted(
        videos, key=lambda v: integer(v.get('views')) / max(1, age_days(v.get('published_at'), today) or 1), reverse=True
    )[:5]
    return {
        'query': query, 'scanned_at_utc': today.isoformat(), 'status': status, 'score': score, 'confidence': confidence,
        'evidence_ok': evidence_ok, 'sample_size': n, 'channels': unique,
        'recent_videos': len(recent), 'median_vpd_lifetime': median_vpd,
        'new_channels_in_sample': len(young_ids), 'young_breakout_channels': len(breakout_ids),
        'top3_views_share': round(top3_share * 100), 'young_breakout_share': round(young_share * 100),
        'observed_growth_vpd': median_growth, 'observed_video_count': len(growth_values),
        'methods': methods, 'notes': notes, 'references': [
            {'title': v.get('title', ''), 'channel': v.get('channel_title', ''),
             'url': v.get('url', ''), 'views': integer(v.get('views')),
             'published_at': v.get('published_at', '')} for v in top_candidates
        ],
    }


MUSIC_NEGATIVES = 'No vocals, no spoken words, no harsh drums, no sudden volume spikes, no clipping, no generic stock melody, no repetitive identical loops.'


def _creative_direction(query):
    q = (query or '').lower()
    if any(t in q for t in ('anxiety', 'healing', 'stress relief', 'calm', 'sleep', 'relax')):
        return {
            'style': 'Gentle healing ambient, warm evolving synth pads, soft felt piano, spacious natural reverberation, very slow harmonic changes, instrumental, restrained dynamics',
            'image': 'Warm minimal bedroom or tranquil landscape at dawn, soft muted natural colors, atmospheric depth, refined cinematic lighting, no text, no logo, widescreen 16:9',
            'purpose': 'descanso e relaxamento',
        }
    if any(t in q for t in ('rain', 'city', 'night', 'lofi', 'cyberpunk')):
        return {
            'style': 'Late-night atmospheric ambient, soft electric piano, mellow synth pads, restrained bass, gentle rainy texture, instrumental and understated',
            'image': 'Rainy quiet city seen from a cozy window at midnight, subtle reflections and soft blue amber lights, cinematic peaceful atmosphere, no text, no logo, widescreen 16:9',
            'purpose': 'foco noturno',
        }
    preset = detect_preset(query, title_keywords([]))
    return {'style': preset['style'], 'image': preset['thumb'] + ', no text, no logo, widescreen 16:9', 'purpose': 'ambientação musical'}


def build_production_plan(query, report, videos, count=3, target_minutes=45, avg_track_minutes=4):
    """Pacote editorial de teste: cada vídeo tem conceito e faixas próprias.

    Sugestões criativas são heurísticas, nunca análise sonora de vídeos do YouTube.
    """
    if not report or report.get('query') != query or not report.get('evidence_ok'):
        raise ValueError('É necessária uma análise real suficiente e do mesmo nicho antes de gerar o plano.')
    if count < 1 or count > 6 or target_minutes < 10 or target_minutes > 180:
        raise ValueError('Parâmetros de planejamento fora do intervalo permitido.')
    direction = _creative_direction(query)
    scene_variants = [
        ('Quiet Beginnings', 'soft morning light; calm introductory progression', 'quiet, close and intimate'),
        ('After Midnight', 'deep midnight atmosphere; spacious sustained harmonies', 'introspective, dreamy and slow'),
        ('The Long Pause', 'minimal atmosphere; slow evolving organic textures', 'floating, minimal and comforting'),
        ('Rain Beyond the Window', 'cozy interior; subtle distant weather texture', 'gentle and reflective'),
        ('A Place to Breathe', 'open landscape; subtle warm horizon', 'light, spacious and hopeful'),
        ('Last Light', 'dim golden light fading into quiet blue', 'peaceful, meditative and restrained'),
    ]
    tracks_per_video = max(3, round(target_minutes / max(2, avg_track_minutes)))
    instrument_variations = [
        'soft felt piano with sparse answering tones',
        'warm evolving analog pads with restrained low drone',
        'gentle bowed textures, long slow harmonic motion',
        'minimal electric piano, delicate ambient shimmer',
        'rounded synth chords, slowly shifting stereo depth',
        'restrained acoustic plucks with soft sustaining pad',
        'muted piano chords, quiet bass undertone',
        'organic field ambience and gentle synthetic harmonics',
        'subtle cello-like pad with suspended chords',
        'light airy arpeggiation with long intervals of silence',
        'tender high-register synth and calm midrange drone',
        'slow soft guitar harmonics washed in reverb',
    ]
    progression_variations = [
        'minor-to-major suspended harmony', 'open fifths and no obvious chorus',
        'modal harmony with gentle tension release', 'slow two-chord structure',
        'minimal non-repeating ambient phrases', 'soft descending harmonic phrase',
    ]
    kw = title_keywords(videos, 8)
    ref_urls = [r['url'] for r in report['references'] if r.get('url')]
    plans = []
    for idx in range(count):
        name, visual, feel = scene_variants[idx]
        music_prompts = []
        for j in range(1, tracks_per_video + 1):
            # Orientações distintas por faixa; não reaproveita o mesmo áudio entre vídeos.
            focus = instrument_variations[(j - 1 + idx * 3) % len(instrument_variations)]
            harmony = progression_variations[(j - 1 + idx) % len(progression_variations)]
            music_prompts.append({
                'track': f'V{idx+1:02d}-T{j:02d}',
                'style': f"{direction['style']}; {feel}; {focus}; {harmony}; gently evolving texture; original instrumental composition; no lead singing.",
                'negative': MUSIC_NEGATIVES,
                'note': 'Avaliar individualmente a faixa e registrar seu direito de uso comercial.',
            })
        title = f'{name} | {query.title()} — Instrumental Mix'
        plans.append({
            'video': idx + 1, 'title': title, 'concept': name,
            'target_duration_minutes': target_minutes, 'target_tracks': tracks_per_video,
            'purpose': direction['purpose'], 'music_style': direction['style'],
            'cover_prompt': direction['image'] + f', scene concept: {visual}',
            'negative_visual_prompt': 'words, watermark, brand marks, UI, clutter, oversaturated glow, recognizable celebrities',
            'description': f'{name}: uma seleção de composições instrumentais originais para {direction["purpose"]}.\n\nMúsicas produzidas para este mix. Capítulos e créditos devem ser inseridos após a montagem.\n\n#AmbientMusic #Instrumental',
            'tracks': music_prompts,
            'research_references': ref_urls[:3],
            'source_keywords': [word for word, _ in kw[:5]],
            'notes': ['A duração é uma meta editorial, não uma promessa até o áudio ser montado.',
                      'Validar título, música, thumbnail e direitos antes de publicar.',
                      'Não reutilizar o mesmo conjunto de músicas em várias versões quase idênticas.'],
        })
    return plans

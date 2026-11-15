"""Motor de Inteligência, Scanner com Saturação/Oceano Azul e Estilos Visuais."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median
import math
import re

MOON_LOGO_SVG = '<svg width="52" height="52" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;"><defs><linearGradient id="moonGrad" x1="6" y1="6" x2="42" y2="42" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#E9D5FF"/><stop offset="50%" stop-color="#9333EA"/><stop offset="100%" stop-color="#3B0764"/></linearGradient><filter id="purpleGlow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="#9333EA" flood-opacity="0.65"/></filter></defs><circle cx="24" cy="24" r="22" fill="#0D0D14" stroke="#27273A" stroke-width="1.5"/><path filter="url(#purpleGlow)" d="M31.5 34.2C23.8 34.2 17.5 27.9 17.5 20.2C17.5 15.6 19.7 11.5 23.1 9.0C15.4 9.7 9.5 16.2 9.5 24.1C9.5 32.5 16.3 39.3 24.7 39.3C30.8 39.3 36.1 35.7 38.5 30.5C36.4 32.8 34.1 34.2 31.5 34.2Z" fill="url(#moonGrad)"/><circle cx="31" cy="15" r="1.5" fill="#F3E8FF" opacity="0.9"/><circle cx="35.5" cy="21" r="1" fill="#A855F7" opacity="0.75"/></svg>'

BRAND_HEADER_HTML = f'<div class="brand-box">{MOON_LOGO_SVG}<div class="brand-text"><div class="brand-title">DARK LAB</div><div class="brand-sub">COMMAND CENTER • V2</div></div></div>'

CUSTOM_CSS = """<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@600;700;800&display=swap');
  html, body, .stApp, p, label, input, button, select, textarea { font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important; }
  [data-testid="stIconMaterial"], [data-testid="stSidebarCollapseButton"] *, [data-testid="collapsedControl"] *, .material-symbols-rounded { font-family: 'Material Symbols Rounded', 'Material Icons' !important; }
  .stApp { background-color: #09090D; color: #E5E7EB; }
  .block-container { padding-top: 1.5rem; max-width: 1440px; }
  h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.03em !important; color: #F9FAFB !important; font-weight: 700 !important; }
  h1 { font-size: 2.0rem !important; }
  h3 { font-size: 1.25rem !important; }
  section[data-testid="stSidebar"] { background-color: #0C0C12 !important; border-right: 1px solid #1F1F2E !important; }
  div[data-testid="stMetric"] { background: linear-gradient(145deg, #12121A, #0D0D14); padding: 16px 18px; border: 1px solid #232334; border-left: 3px solid #8B5CF6; border-radius: 12px; box-shadow: 0 4px 18px rgba(0,0,0,0.4); }
  div[data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif !important; font-size: 1.6rem !important; color: #F3E8FF !important; font-weight: 700 !important; }
  div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 0.82rem !important; font-weight: 500 !important; }
  .eyebrow { text-transform: uppercase; letter-spacing: 0.16em; font-size: 0.70rem; color: #A855F7; font-weight: 700; margin: 0 0 6px 0; }
  .subline { color: #9CA3AF; margin: -6px 0 22px 0; font-size: 0.94rem; }
  .panel { border: 1px solid #232334; border-radius: 12px; padding: 16px 18px; background: linear-gradient(140deg, #13131C, #0E0E15); margin: 4px 0 12px; transition: all 0.2s ease; }
  .panel:hover { border-color: #7C3AED; box-shadow: 0 0 16px rgba(139,92,246,0.12); }
  .panel .name { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700; font-size: 1.04rem; color: #F9FAFB; }
  .panel .meta { font-size: 0.85rem; color: #9CA3AF; margin-top: 6px; line-height: 1.5; }
  .tag { display: inline-block; margin-top: 10px; padding: 3px 10px; border-radius: 6px; background: rgba(139,92,246,0.12); border: 1px solid rgba(168,85,247,0.28); color: #C4B5FD; font-size: 0.72rem; font-weight: 600; }
  div[data-testid="stDataFrame"] { border: 1px solid #232334; border-radius: 10px; background-color: #101017; }
  .stButton button { border-radius: 8px; font-weight: 600; font-size: 0.88rem; border: 1px solid #2C2C40; background-color: #151520; color: #F3F4F6; }
  .stButton button:hover { border-color: #9333EA; color: #F3E8FF; background-color: #1E1830; }
  .stButton button[kind="primary"], button[data-testid="baseButton-primary"] { background: linear-gradient(90deg, #6D28D9, #8B5CF6) !important; border: 1px solid #A855F7 !important; color: #FFFFFF !important; }
  a { color: #C084FC !important; text-decoration: none; }
  .brand-box { display: flex; align-items: center; gap: 14px; padding: 6px 4px 16px 4px; margin-bottom: 10px; border-bottom: 1px solid #1E1E2C; }
  .brand-text { display: flex; flex-direction: column; justify-content: space-between; height: 46px; }
  .brand-title { font-family: 'Space Grotesk', sans-serif !important; font-size: 1.56rem; font-weight: 800; letter-spacing: 0.11em; color: #F9FAFB; line-height: 1.0; white-space: nowrap; }
  .brand-sub { font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.65rem; letter-spacing: 0.155em; color: #A855F7; font-weight: 700; line-height: 1.0; white-space: nowrap; }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(2),
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(3),
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(4),
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(5) {
      background: linear-gradient(90deg, rgba(139,92,246,0.14), rgba(18,18,26,0.2));
      border-left: 2px solid #A855F7; border-radius: 0 8px 8px 0; padding: 5px 10px 5px 8px !important; margin: 3px 0 !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(2) p,
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(3) p,
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(4) p,
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(5) p { color: #E9D5FF !important; font-weight: 600 !important; }
</style>"""

STOPWORDS = {
    "the","and","for","with","from","this","that","your","you","are","not","all",
    "music","video","official","full","mix","playlist","hour","hours","min","best",
    "para","com","uma","das","dos","que","por","sem","mais","seu","sua",
    "de","da","do","em","na","no","as","os","um","a","o","e","ao","ou",
    "2024","2025","2026","2027","4k","hd","60fps","1080p"
}

RADAR_PACKS = {
    "Música Dark & Suno AI (Alta Retenção)": [
        "dark blues music", "medieval tavern ambient", "dark noir jazz saxophone",
        "dark academia classical", "cyberpunk rain lofi", "viking dark folk ambient"
    ],
    "Ambience, Sono & Foco Profundo (Vídeos Longos)": [
        "cozy rain cabin ambience", "deep space ambient sleep", "ancient library rain sounds",
        "dark fantasy dungeon synth", "japanese night rain lofi", "thunderstorm gothic castle"
    ],
    "Canais Dark Narrados / Alto RPM (Gringa)": [
        "stoic philosophy motivation", "ancient civilizations documentary", "dark psychology secrets",
        "unsolved creepy mysteries", "sleep history storytelling", "bizarre historical events"
    ]
}

SUNO_PRESETS = {
    "blues": {
        "style": "Slow Electric Blues, Dark Noir Blues, Vintage Tube Amp, Melancholic Solo Guitar, Late Night Whiskey Bar Atmosphere, 68 BPM",
        "thumb": "Dark moody vintage whiskey bar at night, neon purple and warm amber rim light, silhouette of a blues guitar, rain on window, cinematic 8k",
        "prefixes": ["Noir", "Midnight", "Velvet", "Smoky", "Hollow", "Bourbon"],
        "suffixes": ["Blues Club", "Guitar Sessions", "Night Radio", "Lounge", "Room", "Echoes"]
    },
    "medieval": {
        "style": "Dark Medieval Ambient, Dungeon Synth, Acoustic Lute, Gregorian Distant Choir, Tavern Fireplace Crackling, Fantasy Soundtrack, 72 BPM",
        "thumb": "Ancient stone castle hall lit by torches and purple moonlight, misty medieval tavern, dark fantasy aesthetic, oil painting style, 8k",
        "prefixes": ["Forgotten", "Ancient", "Eldoria", "Shadow", "Iron", "Mystic"],
        "suffixes": ["Tavern", "Chronicles", "Citadel Audio", "Bard", "Sanctum", "Realms"]
    },
    "lofi": {
        "style": "Dark Chillhop, Lo-Fi Rain Beats, Dusty Vinyl Crackle, Mellow Rhodes Piano, Deep Sub Bass, Cozy Late Night Study, 80 BPM",
        "thumb": "Cozy dark bedroom desk overlooking a cyberpunk rainy city at night, purple LED lights, sleeping cat, steaming coffee cup, anime lofi aesthetic",
        "prefixes": ["Lunar", "Rainy", "Neko", "Obsidian", "Quiet", "Neon"],
        "suffixes": ["Lo-Fi", "Tape", "Study Room", "Frequencies", "Beats", "Cafe"]
    },
    "jazz": {
        "style": "Dark Noir Jazz, Slow Tenor Saxophone, Brushed Snare Drum, Upright Walking Bass, Rainy Paris Street Vibe, 65 BPM",
        "thumb": "1940s noir detective street under heavy rain, saxophone shadow under a streetlamp, dark grey and violet tones, cinematic film grain",
        "prefixes": ["Gotham", "Velvet", "Nocturne", "Rainy", "Shadow", "Blue"],
        "suffixes": ["Jazz Club", "Saxophone", "Vinyl", "Society", "Quartet", "Bistro"]
    },
    "academia": {
        "style": "Dark Academia Classical, Melancholic Cello & Violin, Haunting Solo Piano, Victorian Library Rain Ambience, 70 BPM",
        "thumb": "Candlelit gothic Victorian library at midnight, rain hitting tall arched windows, old leather books, moody dark aesthetic, 8k",
        "prefixes": ["Obsidian", "Victorian", "Nocturne", "Ivory", "Raven", "Silent"],
        "suffixes": ["Conservatory", "Sonata", "Library", "Archive", "Chamber", "Studies"]
    },
    "viking": {
        "style": "Nordic Dark Folk, Deep Ritual Frame Drums, Tagelharpa, Throat Singing Drone, Cold Misty Fjord Atmosphere, 66 BPM",
        "thumb": "Ancient Nordic wooden longhouse in a misty dark forest under purple aurora borealis, bonfire embers, cinematic dark folk art, 8k",
        "prefixes": ["Valhalla", "Nordic", "Runic", "Frost", "Odin", "Shadow"],
        "suffixes": ["Drums", "Echoes", "Saga", "Fjord", "Chants", "Sanctuary"]
    },
    "ambient": {
        "style": "Deep Dark Ambient, Ethereal Drone, Cosmic Synthesizer, Slow Reverb Pads, Deep Focus & Sleep Frequency, 60 BPM",
        "thumb": "Lone hooded figure or astronaut looking at a giant purple crescent moon in a dark desolate landscape, cinematic sci-fi ambient, 8k",
        "prefixes": ["Astral", "Void", "Eclipse", "Nebula", "Deep", "Silent"],
        "suffixes": ["Frequencies", "Horizon", "Ambient", "Lab", "Odyssey", "Cosmos"]
    }
}

def integer(value, default=0):
    try: return int(value)
    except (TypeError, ValueError): return default

def iso_date(value):
    if not value: return None
    try: return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError): return None

def age_days(value, now=None):
    dt = iso_date(value)
    if not dt: return None
    now = now or datetime.now(timezone.utc)
    return max(1, (now - dt).days)

def fmt_num(value):
    x = integer(value)
    if abs(x) >= 1_000_000_000: return f'{x / 1_000_000_000:.1f} bi'
    if abs(x) >= 1_000_000: return f'{x / 1_000_000:.1f} mi'
    if abs(x) >= 1_000: return f'{x / 1_000:.1f} mil'
    return f'{x:,}'.replace(',', '.')

def channel_metrics(ch):
    ch = dict(ch)
    ch['age_days'] = age_days(ch.get('published_at')) or 1
    ch['views_per_video'] = round(integer(ch.get('views')) / max(1, integer(ch.get('video_count'))))
    subs = integer(ch.get('subscribers'))
    video_count = integer(ch.get('video_count'))
    efficiency = math.log1p(ch['views_per_video']) / math.log1p(1_000_000)
    freshness = math.exp(-ch['age_days'] / 700)
    consistency = min(video_count, 50) / 50
    ch['exploration_score'] = round(100 * (0.55 * min(efficiency, 1) + 0.30 * freshness + 0.15 * consistency))
    ch['subscribers'] = subs
    return ch

def rank_outliers(videos):
    videos = list(videos)
    values = [integer(v.get('views')) for v in videos if integer(v.get('views')) >= 0]
    baseline = median(values) if values else 0
    output = []
    for v in videos:
        item = dict(v)
        item['outlier_ratio'] = round(integer(v.get('views')) / baseline, 2) if baseline else 0.0
        d = age_days(v.get('published_at'))
        item['views_per_day'] = round(integer(v.get('views')) / d) if d else 0
        output.append(item)
    return sorted(output, key=lambda x: x['outlier_ratio'], reverse=True)

def title_keywords(videos, limit=15):
    words = []
    for v in videos:
        title = str(v.get('title') or '').lower()
        words += [w for w in re.findall(r'[^\W_]+', title, flags=re.UNICODE)
                  if len(w) >= 4 and w not in STOPWORDS and not w.isnumeric()]
    return Counter(words).most_common(limit)

def niche_summary(videos):
    videos = list(videos)
    n_vids = max(1, len(videos))
    values = [integer(v.get('views')) for v in videos]
    days = [age_days(v.get('published_at')) or 90 for v in videos]
    ranked = rank_outliers(videos) if videos else []
    best_outlier = ranked[0]['outlier_ratio'] if ranked else 1.0
    top_video = ranked[0]['title'] if ranked else ''
    vpd_list = [v / max(1, d) for v, d in zip(values, days)]
    med_vpd = round(median(vpd_list)) if vpd_list else 0
    med_views = round(median(values)) if values else 0
    unique_channels = len(set(v.get('channel_id') for v in videos if v.get('channel_id'))) or 1

    diversity_ratio = unique_channels / n_vids
    monopoly_penalty = 1.0 - min(1.0, diversity_ratio)
    recent_ratio = sum(1 for d in days if d <= 60) / n_vids
    stagnation_penalty = 1.0 - recent_ratio
    outlier_relief = min(1.0, best_outlier / 12.0)

    sat_raw = 100 * (0.45 * monopoly_penalty + 0.35 * stagnation_penalty + 0.20 * (1.0 - outlier_relief))
    saturation_score = max(12, min(95, round(sat_raw)))

    if saturation_score <= 45 and med_vpd >= 250:
        market_status = "🟢 Oceano Azul"
    elif saturation_score <= 68:
        market_status = "🟡 Competitivo (Com Brechas)"
    else:
        market_status = "🔴 Saturado (Dominado)"

    vel_score = min(1.0, math.log1p(med_vpd) / math.log1p(6000))
    openness_score = (100 - saturation_score) / 100.0
    opp_score = round(100 * (0.45 * vel_score + 0.35 * openness_score + 0.20 * outlier_relief))

    return {
        'sample_size': len(videos),
        'median_views': med_views,
        'median_views_per_day': med_vpd,
        'channels_in_sample': unique_channels,
        'best_outlier': best_outlier,
        'top_video': top_video,
        'saturation_score': saturation_score,
        'market_status': market_status,
        'opportunity_score': opp_score
    }

def revenue_range(monthly_views, rpm_low, rpm_high):
    views = max(0, integer(monthly_views))
    a, b = sorted((max(0, rpm_low), max(0, rpm_high)))
    return views * a / 1000, views * b / 1000

def detect_preset(query: str, keywords: list[tuple[str, int]]):
    bag = (query + " " + " ".join(w for w, _ in keywords)).lower()
    for key, preset in SUNO_PRESETS.items():
        if key in bag: return preset
    if "rain" in bag or "chill" in bag or "cyberpunk" in bag: return SUNO_PRESETS["lofi"]
    if "classical" in bag or "piano" in bag or "library" in bag: return SUNO_PRESETS["academia"]
    if "folk" in bag or "nordic" in bag: return SUNO_PRESETS["viking"]
    return SUNO_PRESETS["ambient"]

def generate_action_blueprint(query: str, videos: list[dict], channels: list[dict] = None):
    ranked = rank_outliers(videos) if videos else []
    kw = title_keywords(videos, 12)
    top_words = [w.capitalize() for w, _ in kw[:6]] or ["Midnight", "Dark", "Shadow", "Deep", "Rain", "Session"]
    preset = detect_preset(query, kw)
    summary = niche_summary(videos)
    best_ratio = summary['best_outlier']
    sat = summary['saturation_score']
    status = summary['market_status']

    if "Oceano Azul" in status:
        verdict = f"{status} — Saturação Baixa ({sat}%) e Alta Demanda!"
        advice = "Poucos canais dominando e vídeos recentes furando a bolha com facilidade. Momento ideal para entrar."
    elif "Competitivo" in status:
        verdict = f"{status} — Saturação Moderada ({sat}%)"
        advice = "Mercado ativo com concorrentes estabelecidos, mas ainda aceitando canais novos que usam títulos de alto contraste (Outliers)."
    else:
        verdict = f"{status} — Saturação Alta ({sat}%)"
        advice = "Tráfego concentrado em poucos canais veteranos. Para entrar aqui, sub-niche o tema (misture 2 estilos) em vez de bater de frente."

    channel_names = [f"{p} {top_words[i % len(top_words)]} {preset['suffixes'][i % len(preset['suffixes'])]}" for i, p in enumerate(preset["prefixes"])]
    w1, w2, w3 = top_words[0], top_words[1 % len(top_words)], top_words[2 % len(top_words)]
    title_ideas = [
        f"You're in a {w1} {w2} Room and It's Raining Outside | {query.title()} Mix",
        f"3 Hours of {w1} & {w2} {query.title()} for Deep Focus, Study and Late Night Work",
        f"When the Night Feels Endless... ({w1} {w3} {query.title()} Playlist)",
        f"{w1} {w2} Sessions • Slow & Melancholic {query.title()} (No Ads / Instrumental)",
        f"Late Night {w1} Atmosphere | {query.title()} to Relax & Escape Reality",
        f"The Sound of a Forgotten {w1} | Dark {query.title()} & {w3} Ambience"
    ]
    suno_prompts = [
        f"[Prompt Principal] {preset['style']}, inspired by {w1.lower()} and {w2.lower()} mood, instrumental only, high fidelity, seamless loop",
        f"[Variação Melancólica] Slow atmospheric {query.lower()}, {w1.lower()} vibe, deep bass, warm analog reverb, emotional and hypnotic, instrumental",
        f"[Variação Chuva/Noite] Late night {query.lower()} with subtle rain texture, {preset['style']}, relaxing, dark aesthetic, no vocals"
    ]

    return {
        "verdict": verdict, "advice": advice,
        "median_views": summary["median_views"], "median_vpd": summary["median_views_per_day"],
        "best_outlier": best_ratio, "saturation_score": sat, "market_status": status,
        "top_words": top_words, "channel_names": channel_names[:6],
        "title_ideas": title_ideas, "suno_prompts": suno_prompts,
        "thumb_prompt": preset["thumb"], "top_outliers": ranked[:3]
    }

def generate_bulk_schedule(niche: str, count: int, start_date, post_time: str, days_filter: list[int], videos_sample: list[dict] = None):
    bp = generate_action_blueprint(niche, videos_sample or [])
    words = bp["top_words"]
    base_suno = bp["suno_prompts"][0].replace("[Prompt Principal] ", "")
    base_thumb = bp["thumb_prompt"]
    atmospheres = ["Rainy Midnight", "Velvet Shadow", "Empty Street", "Silent Cigar Lounge", "Moonlit Window", "Forgotten Tavern", "Deep Obsidian", "3 AM Insomnia"]
    hooks = ["Music for Late Night Focus", "1 Hour Instrumental Mix", "Slow & Melancholic Ambience", "Dark Aesthetic Playlist • No Vocals"]

    rows, cur_date, idx = [], start_date, 1
    days_filter = days_filter or [0, 1, 2, 3, 4, 5, 6]
    while idx <= count:
        if cur_date.weekday() in days_filter:
            atm = atmospheres[(idx - 1) % len(atmospheres)]
            hk = hooks[(idx - 1) % len(hooks)]
            kw = words[(idx - 1) % len(words)]
            rows.append({
                "Vídeo #": f"#{idx:03d}", "Data": cur_date.strftime("%d/%m/%Y"), "Horário": post_time,
                "Título Pronto (YouTube)": f"{atm} • {kw} {niche.title()} | {hk} ( Vol. {idx:02d} )",
                "Prompt Suno AI (Música)": f"{base_suno}, theme: {atm.lower()}, track #{idx:02d}",
                "Prompt Thumbnail (Imagem)": f"{base_thumb}, scene: {atm.lower()}, purple and black color grading --ar 16:9",
                "Arquivo Áudio Esperado": f"faixa_{idx:03d}.mp3", "Arquivo Capa Esperado": f"capa_{idx:03d}.png", "Status": "Pendente"
            })
            idx += 1
        cur_date += timedelta(days=1)
    return rows

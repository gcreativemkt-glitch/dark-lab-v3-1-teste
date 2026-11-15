"""Dark Lab V3.1 — Radar amostral, planejamento editorial e capas."""
from __future__ import annotations
import base64
import hashlib
import hmac
import importlib
import io
import os
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone, date
from html import escape
import pandas as pd
import requests
import streamlit as st

import analytics as an
importlib.reload(an)

from analytics import (
    age_days, channel_metrics, fmt_num, niche_summary,
    rank_outliers, revenue_range, generate_action_blueprint, generate_bulk_schedule
)
from demo_data import demo_channels, demo_videos
from storage import Store
from youtube_api import (
    YouTubeError, discover_channels, get_channel,
    latest_channel_videos, search_videos, scan_niche_two_views
)
from opportunity_engine import evaluate_opportunity, build_production_plan
from production_pack import make_production_zip

st.set_page_config(page_title="Dark Lab | Estúdio de Criação", page_icon="🌙", layout="wide")

BRAND_HEADER_HTML = """
<div class="brand-box">
    <div class="brand-main">DARK<span class="brand-highlight">LAB</span></div>
    <div class="brand-sub">YOUTUBE & AUDIO AUTOMATION</div>
    <div class="brand-caption">ESTÚDIO DE CRIAÇÃO</div>
</div>
"""

CUSTOM_CSS = """<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  
  html, body, .stApp, p, label, input, button, select, textarea {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }
  [data-testid="stIconMaterial"], [data-testid="stSidebarCollapseButton"] *, [data-testid="collapsedControl"] *, .material-symbols-rounded {
      font-family: 'Material Symbols Rounded', 'Material Icons' !important;
  }

  /* Fundo principal Preto Fosco Clean */
  .stApp {
      background-color: #0D0D0F;
      color: #F4F4F6;
  }
  .block-container {
      padding-top: 2.2rem;
      padding-bottom: 3rem;
      max-width: 1360px;
  }

  /* Títulos estilo SaaS */
  h1, h2, h3, h4 {
      font-family: 'Inter', sans-serif !important;
      letter-spacing: -0.025em !important;
      color: #FFFFFF !important;
      font-weight: 700 !important;
  }
  h1 { font-size: 2.15rem !important; margin-bottom: 0.2rem !important; }
  h3 { font-size: 1.15rem !important; font-weight: 600 !important; }

  /* Eyebrow (ESTÚDIO CRIATIVO) e Subtítulo */
  .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
      color: #8B5CF6;
      font-weight: 700;
      margin: 0 0 6px 0;
  }
  .subline {
      color: #8E8E93;
      margin: -4px 0 28px 0;
      font-size: 0.92rem;
      line-height: 1.5;
      max-width: 780px;
  }

  /* Barra Lateral Clean & Logo Alinhada */
  section[data-testid="stSidebar"] {
      background-color: #111114 !important;
      border-right: 1px solid #1F1F24 !important;
  }
  .brand-box {
      padding: 6px 4px 18px 4px;
      margin-bottom: 14px;
      border-bottom: 1px solid #1F1F24;
  }
  .brand-main {
      font-size: 2.32rem;
      font-weight: 900;
      letter-spacing: 0.045em;
      color: #FFFFFF;
      line-height: 1.0;
      display: block;
  }
  .brand-highlight {
      color: #8B5CF6;
      font-weight: 400;
      margin-left: 4px;
  }
  .brand-sub {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.085em;
      color: #D4D4D8;
      margin-top: 6px;
  }
  .brand-caption {
      font-size: 0.60rem;
      letter-spacing: 0.12em;
      color: #71717A;
      margin-top: 2px;
  }

  /* Navegação Lateral estilo Menu Flat (Sem bolinhas de rádio) */
  section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
      display: none !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label {
      padding: 10px 14px !important;
      border-radius: 10px !important;
      margin: 4px 0 !important;
      transition: all 0.15s ease;
      border: 1px solid transparent;
      width: 100%;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
      color: #A1A1AA !important;
      font-size: 0.90rem !important;
      font-weight: 500 !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
      background-color: #18181C !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
      color: #F4F4F6 !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
      background-color: #1F1F28 !important;
      border: 1px solid #3B3B4F !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
      color: #FFFFFF !important;
      font-weight: 600 !important;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::before {
      content: "●";
      color: #8B5CF6;
      font-size: 0.75rem;
      margin-right: 10px;
  }

  /* Abas (Tabs) em formato de Botões Arredondados Separados (Zero Poluição Visual) */
  div[data-baseweb="tab-list"] {
      gap: 12px !important;
      border-bottom: none !important;
      padding-bottom: 10px !important;
      flex-wrap: wrap !important;
  }
  button[data-baseweb="tab"] {
      background-color: #16161C !important;
      border: 1px solid #282834 !important;
      border-radius: 10px !important;
      padding: 10px 20px !important;
      color: #A1A1AA !important;
      font-weight: 600 !important;
      font-size: 0.88rem !important;
      transition: all 0.18s ease !important;
      margin: 0 !important;
  }
  button[data-baseweb="tab"]:hover {
      border-color: #6D28D9 !important;
      color: #FFFFFF !important;
      background-color: #1E1E26 !important;
  }
  button[data-baseweb="tab"][aria-selected="true"] {
      background-color: #7C3AED !important;
      border-color: #8B5CF6 !important;
      color: #FFFFFF !important;
      box-shadow: 0 4px 14px rgba(124, 58, 237, 0.32) !important;
  }
  div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {
      display: none !important;
  }

  /* Cards e Formulários */
  div[data-testid="stForm"] {
      background-color: #141417 !important;
      border: 1px solid #242429 !important;
      border-radius: 12px !important;
      padding: 24px !important;
  }

  /* Cards Visuais de Canais e Vídeos */
  .media-card {
      background-color: #141418;
      border: 1px solid #24242C;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
      transition: border-color 0.15s ease;
  }
  .media-card:hover {
      border-color: #6D28D9;
  }
  .media-title {
      font-weight: 600;
      font-size: 0.95rem;
      color: #FFFFFF;
      margin: 10px 0 6px 0;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 2.6em;
  }
  .media-meta {
      font-size: 0.80rem;
      color: #9CA3AF;
      line-height: 1.5;
  }

  /* Rótulos dos Inputs em Caixa Alta Clean */
  .stTextInput label p, .stSelectbox label p, .stNumberInput label p, .stSlider label p, .stDateInput label p, .stTextArea label p, .stFileUploader label p {
      text-transform: uppercase !important;
      font-size: 0.72rem !important;
      letter-spacing: 0.06em !important;
      color: #A1A1AA !important;
      font-weight: 600 !important;
  }

  /* Caixas de Input Escuras */
  div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] > div {
      background-color: #1A1A1E !important;
      border: 1px solid #2A2A32 !important;
      border-radius: 8px !important;
      color: #F4F4F6 !important;
  }
  div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
      border-color: #8B5CF6 !important;
      box-shadow: 0 0 0 1px #8B5CF6 !important;
  }

  /* Métricas Clean */
   div[data-testid="stMetric"] {
      background-color: #141417;
      padding: 18px 20px;
      border: 1px solid #242429;
      border-radius: 10px;
  }
  div[data-testid="stMetricValue"] {
      font-size: 1.65rem !important;
      color: #FFFFFF !important;
      font-weight: 700 !important;
  }
  div[data-testid="stMetricLabel"] {
      color: #8E8E93 !important;
      font-size: 0.78rem !important;
      text-transform: uppercase !important;
      letter-spacing: 0.05em !important;
  }

  /* Painéis Internos */
  .panel {
      border: 1px solid #242429;
      border-radius: 10px;
      padding: 18px 20px;
      background-color: #141417;
      margin: 6px 0 14px;
      transition: border-color 0.15s ease;
  }
  .panel:hover {
      border-color: #3F3F46;
  }
  .panel .name {
      font-weight: 600;
      font-size: 1.02rem;
      color: #FFFFFF;
  }
  .panel .meta {
      font-size: 0.88rem;
      color: #A1A1AA;
      margin-top: 6px;
      line-height: 1.5;
  }
  .tag {
      display: inline-block;
      margin-top: 12px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(124, 58, 237, 0.14);
      border: 1px solid rgba(139, 92, 246, 0.3);
      color: #C4B5FD;
      font-size: 0.74rem;
      font-weight: 500;
  }

  /* Botões Sólidos Roxo / Cinza */
  .stButton button, .stDownloadButton button, .stLinkButton a {
      border-radius: 8px !important;
      font-weight: 600 !important;
      font-size: 0.85rem !important;
      padding: 0.5rem 1.1rem !important;
      border: 1px solid #2E2E36 !important;
      background-color: #1A1A1F !important;
      color: #E4E4E7 !important;
      transition: all 0.15s ease;
  }
  .stButton button:hover, .stDownloadButton button:hover, .stLinkButton a:hover {
      border-color: #8B5CF6 !important;
      color: #FFFFFF !important;
      background-color: #24242C !important;
  }
  .stButton button[kind="primary"], button[data-testid="baseButton-primary"], .stDownloadButton button[kind="primary"] {
      background: #7C3AED !important;
      border: 1px solid #8B5CF6 !important;
      color: #FFFFFF !important;
  }
  .stButton button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover, .stDownloadButton button[kind="primary"]:hover {
      background: #6D28D9 !important;
  }

  div[data-testid="stDataFrame"] {
      border: 1px solid #242429;
      border-radius: 10px;
      background-color: #141417;
  }
  a { color: #A78BFA !important; text-decoration: none; }
</style>"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DEFAULT_PACKS = {
    "Micro-Dores Emocionais & Playlists (Alta Retenção)": [
        "music for overthinking at 3am",
        "ambient music for lonely nights",
        "songs for when you feel empty",
        "late night drive melancholic lofi",
        "healing ambient music for anxiety",
        "dark ambient for deep focus"
    ],
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

RADAR_PACKS = {**DEFAULT_PACKS, **getattr(an, "RADAR_PACKS", {})}

def setting(key, fallback=""):
    try:
        return str(st.secrets.get(key, os.getenv(key, fallback))).strip()
    except Exception:
        return str(os.getenv(key, fallback)).strip()

def valid_setting(val):
    return bool(val) and not val.startswith(("COLE_", "SENHA_FORTE_", "CHAVE_SECRETA_", "https://seu-"))

API_KEY = st.session_state.get("custom_api_key") or setting("YOUTUBE_API_KEY")
PASSWORD = setting("APP_PASSWORD")
SUPA_URL = setting("SUPABASE_URL")
SUPA_KEY = setting("SUPABASE_SERVICE_KEY")
HAS_REAL_KEY = valid_setting(API_KEY)
HAS_DB = valid_setting(SUPA_URL) and valid_setting(SUPA_KEY)

# AUTENTICAÇÃO: estado por sessão, nunca cache global ou token na URL.
# Uma sessão autenticada não libera automaticamente acesso às demais.
if not valid_setting(PASSWORD) and (HAS_REAL_KEY or HAS_DB or valid_setting(setting("FAL_API_KEY")) or valid_setting(setting("GEMINI_API_KEY"))):
    st.error("Configure APP_PASSWORD nos segredos antes de usar integrações pagas ou dados privados.")
    st.stop()
if valid_setting(PASSWORD):
    last_login = st.session_state.get("authenticated_at")
    still_valid = False
    if last_login and st.session_state.get("authenticated"):
        try:
            still_valid = (datetime.now(timezone.utc) - datetime.fromisoformat(last_login)) < timedelta(hours=24)
        except (TypeError, ValueError):
            pass
    if not still_valid:
        st.session_state["authenticated"] = False
        st.markdown(BRAND_HEADER_HTML, unsafe_allow_html=True)
        with st.form("auth_form"):
            typed = st.text_input("Senha do aplicativo", type="password")
            entered = st.form_submit_button("Entrar no Estúdio", type="primary", use_container_width=True)
        if entered:
            if hmac.compare_digest(typed.encode("utf-8"), PASSWORD.encode("utf-8")):
                st.session_state["authenticated"] = True
                st.session_state["authenticated_at"] = datetime.now(timezone.utc).isoformat()
                st.rerun()
            else:
                st.error("Senha incorreta.")
        st.stop()

store = Store(SUPA_URL if HAS_DB else "", SUPA_KEY if HAS_DB else "")

def page_header(title, subtitle, eyebrow="ESTÚDIO CRIATIVO"):
    st.markdown(f'<div class="eyebrow">{escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="subline">{escape(subtitle)}</p>', unsafe_allow_html=True)

def panel(title, text, tag=""):
    badge = f'<div class="tag">{escape(tag)}</div>' if tag else ""
    st.markdown(f'<div class="panel"><div class="name">{escape(title)}</div><div class="meta">{escape(text)}</div>{badge}</div>', unsafe_allow_html=True)

def to_csv(rows, name, label="Baixar Planilha CSV"):
    if rows:
        df = pd.DataFrame(rows)
        st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"), file_name=name, mime="text/csv", key=f"dl_{name}_{len(rows)}")

def show_channels(rows):
    rows = [channel_metrics(c) for c in rows]
    if not rows:
        st.warning("Nenhum canal encontrado na amostra.")
        return
    rows_sorted = sorted(rows, key=lambda x: x.get("exploration_score", 0), reverse=True)
    
    # Grade visual de 3 colunas com miniaturas grandes (padrão Radar de Capas)
    cols = st.columns(3)
    for idx, c in enumerate(rows_sorted):
        with cols[idx % 3]:
            with st.container(border=True):
                thumb = c.get("thumbnail") or "https://via.placeholder.com/320x180/181824/A855F7?text=CANAL"
                st.image(thumb, use_container_width=True)
                st.markdown(f"#### {c['title']}")
                st.caption(
                    f"⭐ **Score Dark Lab:** {c['exploration_score']}/100  \n"
                    f"👥 **Inscritos:** {fmt_num(c.get('subscribers', 0))} · ⏳ **Idade:** {c['age_days']} dias  \n"
                    f"👁️ **Views totais:** {fmt_num(c['views'])} ({fmt_num(c['views_per_video'])} views/vídeo)"
                )
                if c.get("url"):
                    st.link_button("Abrir Canal no YouTube ↗", c["url"], use_container_width=True)

    with st.expander("Ver em formato de planilha / Exportar CSV"):
        to_csv(rows_sorted, "darklab_canais.csv")

def show_videos(videos, outliers=False):
    if not videos:
        return
    rows = rank_outliers(videos) if outliers else videos
    
    # Grade visual de 3 colunas com thumbnails grandes em alta definição
    cols = st.columns(3)
    for idx, v in enumerate(rows):
        with cols[idx % 3]:
            with st.container(border=True):
                vid_id = v.get("video_id") or v.get("id")
                thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else (v.get("thumbnail") or "https://via.placeholder.com/320x180/181824/A855F7?text=VIDEO")
                st.image(thumb, use_container_width=True)
                st.markdown(f"**{v['title'][:65]}**")
                vpd = round(v["views"] / max(1, age_days(v.get("published_at")) or 1))
                same_channel = len({x.get('channel_id') for x in videos if x.get('channel_id')}) <= 1
                out_label = "Outlier no canal" if same_channel else "Relativo à amostra"
                out_str = f" · 🔥 **{out_label}:** {v.get('outlier_ratio', 1.0)}×" if outliers else ""
                st.caption(
                    f"📺 **{v.get('channel_title', 'Canal')}**  \n"
                    f"👁️ **{fmt_num(v['views'])} views** ({fmt_num(vpd)}/dia){out_str}  \n"
                    f"📅 Publicado em: {str(v.get('published_at', ''))[:10]}"
                )
                if v.get("url"):
                    st.link_button("Assistir no YouTube ↗", v["url"], use_container_width=True)

    with st.expander("Ver em formato de planilha / Exportar CSV"):
        to_csv(rows, "darklab_videos.csv")

def render_copiloto_mastigado(query: str, videos: list[dict], channels: list[dict] = None, report: dict = None):
    """Mostra o MESMO relatório que fundamentou o ranking do Scanner."""
    if not videos:
        st.warning("Sem vídeos na amostra desse nicho.")
        return
    report = report or evaluate_opportunity(query, videos, channels or [], methods=1)
    st.markdown("---")
    st.subheader(f"Relatório estratégico — {query}")
    st.info(f"**{report['status']}** · Confiança: **{report['confidence']}** · Índice exploratório: {report['score']}/100")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vídeos amostrados", report['sample_size'])
    c2.metric("Canais distintos", report['channels'])
    c3.metric("Novos canais em destaque", report['young_breakout_channels'])
    c4.metric("Views/dia históricas (mediana)", fmt_num(report['median_vpd_lifetime']))
    st.caption("Views/dia históricas = views acumuladas ÷ dias desde a publicação; NÃO significa crescimento atual.")
    c5, c6 = st.columns(2)
    c5.metric("Views dos 3 maiores canais da amostra", f"{report['top3_views_share']}%")
    c6.metric("Crescimento observado (views/dia)",
              fmt_num(report['observed_growth_vpd']) if report['observed_growth_vpd'] is not None else "Aguardando nova coleta")
    with st.expander("Como interpretar e conferir as evidências", expanded=True):
        st.write("Esta é uma triagem de uma AMOSTRA pública, não uma previsão de faturamento ou um censo da concorrência.")
        for note in report['notes']:
            st.write("• " + note)
        for ref in report['references'][:5]:
            if ref['url']:
                st.markdown(f"- [{ref['title']}]({ref['url']}) — {ref['channel']} ({fmt_num(ref['views'])} views)")
    if demo:
        st.warning("DEMONSTRAÇÃO: os dados acima são inventados. Não use para decidir um nicho real.")
        return
    if not report['evidence_ok']:
        st.warning("Dados insuficientes para montar o plano de produção. Refaça a pesquisa com mais termos/mais amostras.")
        return
    example_plans = build_production_plan(query, report, videos, count=2, target_minutes=40)
    st.markdown("#### Prévia da produção recomendada")
    st.caption("Sugestões editoriais geradas por regras, não por análise do áudio dos vídeos concorrentes.")
    for sample_plan in example_plans:
        st.markdown(f"**{sample_plan['title']}** — {sample_plan['target_tracks']} faixas originais (meta {sample_plan['target_duration_minutes']} min)")
        with st.expander(f"Estilo e capa — vídeo {sample_plan['video']}"):
            st.code(sample_plan['music_style'], language='text')
            st.code(sample_plan['cover_prompt'], language='text')
    if st.button(f'Criar pacote de produção para "{query}"', key=f"plan_{query}",
                 use_container_width=True, type="primary"):
        st.session_state['planner_research'] = {'query': query, 'videos': videos, 'report': report}
        st.success('Pesquisa transferida! Abra "Planejador & Suno" para baixar o pacote pronto.')
    if st.button(f'Salvar "{query}" nos meus Projetos', key=f"proj_{query}", use_container_width=True):
        store.add_project(f"Canal — {query.title()}", query, "Pesquisa", f"Amostra: {report['sample_size']} vídeos; {report['status']}")
        st.success("Pesquisa salva nos projetos!")

with st.sidebar:
    st.markdown(BRAND_HEADER_HTML, unsafe_allow_html=True)
    demo = st.toggle("Modo demonstração", value=not HAS_REAL_KEY) if HAS_REAL_KEY else True
    st.caption("🟣 Demonstração ativa" if demo else "🟢 YouTube API Conectada")
    st.markdown('<div style="font-size:0.65rem; font-weight:700; color:#71717A; letter-spacing:0.1em; margin: 14px 0 6px 4px;">FLUXO PRINCIPAL</div>', unsafe_allow_html=True)
    page = st.radio("NAVEGAÇÃO", [
        "Scanner de Nichos",
        "Copiloto & Radar",
        "Planejador & Suno",
        "Estúdio de Capas",
        "Espião & Ferramentas",
    ], label_visibility="collapsed")
    st.divider()
    if valid_setting(PASSWORD) and st.button("Sair / Bloquear", use_container_width=True):
        st.session_state.pop("authenticated_at", None)
        st.session_state["authenticated"] = False
        st.rerun()

if page == "Scanner de Nichos":
    page_header("Radar de Oportunidades — Oceano Azul", "Encontre sinais de entrada de canais novos e tração recente usando amostras reais, com transparência sobre as limitações.")
    if demo:
        st.warning("MODO DEMONSTRAÇÃO — os resultados abaixo NÃO são pesquisas do YouTube e não servem para escolher um nicho.")
    st.caption("Cada termo consulta até 25 vídeos populares + 25 recentes. Limite de coleta para reduzir uso de cota; não cobre todo o YouTube.")
    music_packs = {n: x for n, x in RADAR_PACKS.items() if "Música" in n or "Ambience" in n}
    with st.form("scanner_form"):
        st.markdown("#### Escolha o território de pesquisa")
        c1, c2 = st.columns([2.2, 1])
        pack_choice = c1.selectbox("Grupo de micronichos", list(music_packs.keys()))
        periodo_scan = c2.selectbox("Vídeos publicados", ["Últimos 90 dias", "Últimos 180 dias", "Últimos 365 dias"])
        scan_btn = st.form_submit_button("Encontrar oportunidades", type="primary")
    if scan_btn:
        terms = music_packs[pack_choice]
        after_days = {"Últimos 90 dias": 90, "Últimos 180 dias": 180, "Últimos 365 dias": 365}[periodo_scan]
        dt = (datetime.now(timezone.utc) - timedelta(days=after_days)).isoformat().replace("+00:00", "Z")
        scan_rows, scan_context, all_videos = [], {}, []
        errors = []
        with st.spinner("Pesquisando vídeos, canais recentes e comparando padrões na amostra..."):
            for idx, term in enumerate(terms):
                try:
                    if demo:
                        vids = [dict(v, video_id=v.get('video_id') or f'demo_{idx}_{j}',
                                     views=int(v['views'] * max(0.4, 1.4 - idx * 0.18)))
                                for j, v in enumerate(demo_videos())]
                        channels = demo_channels(term)
                    else:
                        channels, vids = scan_niche_two_views(term, API_KEY, dt, each_limit=25)
                    try:
                        growth = store.observed_video_growth(vids) if not demo else {}
                    except (RuntimeError, ValueError) as exc:
                        errors.append(f"Histórico indisponível para {term}: {exc}. A análise prossegue sem crescimento observado.")
                        growth = {}
                    report = evaluate_opportunity(term, vids, channels, growth, methods=2 if not demo else 1)
                    scan_context[term] = {'videos': vids, 'channels': channels, 'report': report}
                    all_videos.extend(vids)
                    scan_rows.append({
                        'Nicho': term, 'Diagnóstico': report['status'],
                        'Índice exploratório': report['score'], 'Confiança': report['confidence'],
                        'Amostra de vídeos': report['sample_size'], 'Canais': report['channels'],
                        'Canais novos em destaque': report['young_breakout_channels'],
                        'Views/dia históricas (mediana)': report['median_vpd_lifetime'],
                        'Concentração top 3 (%)': report['top3_views_share'],
                        'Crescimento real observado/dia': report['observed_growth_vpd'],
                        '_valid': report['evidence_ok'],
                    })
                except (YouTubeError, RuntimeError) as exc:
                    errors.append(f"{term}: {exc}")
        if not demo and all_videos:
            try:
                store.save_video_snapshots(all_videos)
            except (RuntimeError, ValueError) as exc:
                errors.append(f"Histórico de visualizações não salvo: {exc}. Se usa Supabase, execute a atualização do supabase.sql.")
        if errors:
            for err in errors:
                st.warning(err)
        st.session_state['auto_scan_results'] = sorted(scan_rows, key=lambda x: (x['_valid'], x['Índice exploratório']), reverse=True)
        st.session_state['auto_scan_context'] = scan_context
    auto_results = st.session_state.get('auto_scan_results', [])
    auto_context = st.session_state.get('auto_scan_context', {})
    if auto_results:
        top = auto_results[0]
        if top['_valid'] and not demo:
            panel(f"Prioridade para investigar: {top['Nicho']}",
                  f"{top['Diagnóstico']} · Índice exploratório {top['Índice exploratório']}/100 · Confiança {top['Confiança']}. Reveja as referências antes de produzir.",
                  "Recomendação fundamentada na amostra")
        else:
            st.warning("Nenhum nicho passou pelo mínimo de evidências nesta coleta. Não existe vencedor comprovado.")
        shown = [{k: v for k, v in row.items() if k != '_valid'} for row in auto_results]
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
        st.caption("O índice não é porcentagem de sucesso ou de saturação. Repetir uma pesquisa em outro dia ajuda a medir crescimento observado.")
        chosen = st.selectbox("Abrir relatório e prévia da produção", [r['Nicho'] for r in auto_results])
        if chosen in auto_context:
            ctx = auto_context[chosen]
            render_copiloto_mastigado(chosen, ctx['videos'], ctx['channels'], ctx['report'])

elif page == "Copiloto & Radar":
    page_header("Copiloto & Radar de Canais", "Filtre canais recentes que estão explodindo e veja as capas e vídeos campeões em tamanho grande.")
    with st.form("radar_search"):
        st.markdown("#### Briefing de Pesquisa")
        c1, c2, c3 = st.columns([2.2, 1, 1])
        query = c1.text_input("Nicho, Micro-Dor ou Estilo", st.session_state.get("planner_niche", "healing ambient music for anxiety"))
        order = c2.selectbox("Ordenar busca", ["Mais vistos", "Mais recentes"])
        scope = c3.selectbox("Vídeos publicados", ["Últimos 90 dias", "Qualquer data", "Último ano"])
        c4, c5, c6 = st.columns(3)
        age_limit = c4.slider("Idade máxima do canal (meses)", 1, 120, 6)
        max_subs = c5.number_input("Máximo de inscritos (0 = sem limite)", min_value=0, value=30000, step=5000)
        min_views = c6.number_input("Views mínimas do canal", min_value=0, value=50000, step=50000)
        submitted = st.form_submit_button("Pesquisar e montar análise", type="primary")
    if submitted and query.strip():
        after = {"Qualquer data": None, "Últimos 90 dias": 90, "Último ano": 365}[scope]
        dt = (datetime.now(timezone.utc) - timedelta(days=after)).isoformat().replace("+00:00", "Z") if after else None
        try:
            with st.spinner("Consultando YouTube..."):
                channels, sample = (demo_channels(), demo_videos()) if demo else scan_niche_two_views(query, API_KEY, dt, each_limit=25)
            st.session_state["radar_query"], st.session_state["radar_channels"], st.session_state["radar_sample"] = query, channels, sample
        except YouTubeError as exc:
            st.error(str(exc))
    results, sample_videos = st.session_state.get("radar_channels", []), st.session_state.get("radar_sample", [])
    if results:
        filtered = [c for c in results if (age_days(c.get("published_at")) or 99999) <= age_limit * 30.44 and c.get("views", 0) >= min_views and (max_subs == 0 or (c.get("subscribers") or 0) <= max_subs)]
        render_copiloto_mastigado(st.session_state.get("radar_query", query), sample_videos, results)
        st.markdown("---")
        tab_c, tab_v = st.tabs([
            f"Canais Encontrados ({len(filtered)})",
            f"Vídeos da Amostra ({len(sample_videos)})"
        ])
        with tab_c:
            show_channels(filtered)
        with tab_v:
            show_videos(sample_videos, outliers=True)

elif page == "Planejador & Suno":
    page_header("Plano de Produção — Suno & Capas", "O pacote utiliza o mesmo relatório real do Scanner. Crie poucos mixes originais, com prompts por faixa, capas e checklists.")
    research = st.session_state.get('planner_research')
    if demo:
        st.warning("Você está em demonstração. Desative-a e faça uma pesquisa real para gerar o pacote de produção.")
    elif not research:
        st.info("Primeiro abra o Scanner ou o Copiloto, faça uma pesquisa real e clique em 'Criar pacote de produção'. Assim evitamos planejar com dados inventados ou de outro nicho.")
    else:
        niche_in = research['query']
        report = research['report']
        st.info(f"**Nicho selecionado:** {niche_in} · **Diagnóstico:** {report['status']} · **Confiança:** {report['confidence']}")
        with st.form("production_form"):
            c1, c2 = st.columns(2)
            count = c1.selectbox("Quantidade de vídeos no lote piloto", [2, 3, 4, 6], index=0)
            target = c2.selectbox("Duração-alvo por vídeo", [30, 40, 45, 60], index=1)
            submit = st.form_submit_button("Gerar pacote completo", type="primary")
        if submit:
            try:
                plans = build_production_plan(niche_in, report, research['videos'], count=count, target_minutes=target)
                st.session_state['generated_production'] = {'niche': niche_in, 'report': report, 'plans': plans}
            except ValueError as exc:
                st.error(str(exc))
        output = st.session_state.get('generated_production')
        if (output and output['niche'] == niche_in and
                output['report'].get('scanned_at_utc') == report.get('scanned_at_utc')):
            plans = output['plans']
            payload = make_production_zip(niche_in, report, plans)
            st.download_button("Baixar plano completo em ZIP", data=payload,
                               file_name='darklab_pacote_producao.zip', mime='application/zip',
                               type='primary', use_container_width=True)
            st.caption("O ZIP inclui justificativa, referências reais, dois ou mais roteiros com faixas individuais, prompts Suno e capas. Não contém áudio gerado.")
            for plan in plans:
                with st.expander(f"Vídeo {plan['video']:02d} — {plan['title']}", expanded=(plan['video'] == 1)):
                    st.write(f"**Conceito:** {plan['concept']} · **Meta:** {plan['target_duration_minutes']} min · **Faixas:** {plan['target_tracks']}")
                    st.markdown("**Prompt de capa**")
                    st.code(plan['cover_prompt'], language='text')
                    st.markdown("**Prompts do Suno**")
                    for track in plan['tracks']:
                        st.markdown(f"**{track['track']}**")
                        st.code(track['style'], language='text')
                        st.caption('Negative / Exclude: ' + track['negative'])
                    st.markdown("**Descrição preliminar**")
                    st.code(plan['description'], language='text')

elif page == "Estúdio de Capas":
    page_header("Estúdio de Capas & Referências", "Crie capas 16:9 na Fal.ai e estude referências visuais no YouTube.")
    
    tab_capas, tab_radar = st.tabs([
        "Gerador de Capas (Fal.ai)",
        "Radar & Dissecador de Capas"
    ])
    
    with tab_capas:
        with st.form("fal_batch_thumbs"):
            st.markdown("#### Lote de Capas 16:9 (Flux)")
            
            chave_manual = st.text_input(
                "Chave da Fal.ai (Deixe em branco para usar a do Secrets, ou cole aqui para forçar)",
                type="password"
            )
            
            default_prompt = (
                "Digital concept art, stylized illustration. A lone modern astronaut sitting on a concrete ledge overlooking a midnight cyberpunk skyline. "
                "High contrast, sharp clean lines, vibrant neon cyan and deep magenta glow reflecting off the helmet visor. Deep midnight blue background, "
                "starry night sky, cozy and melancholic mood, vibrant color grading, trending on ArtStation, 8k, 16:9."
            )
            prompt_thumb = st.text_area("Prompt Base da Identidade Visual", value=default_prompt, height=110)
            c1, c2, c3 = st.columns(3)
            qtd_capas = c1.slider("Quantidade de Capas", min_value=1, max_value=30, value=5)
            modelo_fal = c2.selectbox("Modelo Fal.ai", [
                "fal-ai/flux/schnell (Ultra Rápido & Barato)",
                "fal-ai/flux/dev (Alta Qualidade)"
            ])
            prefixo = c3.text_input("Prefixo dos Arquivos", value="capa_astronauta")
            gerar_btn = st.form_submit_button("Gerar Lote de Capas na Fal.ai", type="primary")
            
        if gerar_btn:
            raw_key = chave_manual.strip() or setting("FAL_API_KEY").strip() or setting("FAL_KEY").strip()
            fal_key = raw_key.replace("Key ", "").replace("Bearer ", "").strip().strip('"').strip("'")
            
            if not fal_key:
                st.error("Nenhuma chave encontrada. Cole sua chave no campo acima ou no secrets.toml!")
            else:
                endpoint = "https://fal.run/" + modelo_fal.split(" ")[0]
                headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
                imgs_geradas = []
                barra = st.progress(0, text="Iniciando geração na Fal.ai...")
                
                for i in range(qtd_capas):
                    barra.progress((i) / qtd_capas, text=f"Gerando capa {i+1} de {qtd_capas}...")
                    payload = {
                        "prompt": prompt_thumb,
                        "image_size": "landscape_16_9",
                        "num_images": 1,
                        "enable_safety_checker": True
                    }
                    try:
                        resp = requests.post(endpoint, headers=headers, json=payload, timeout=90)
                        if resp.status_code != 200:
                            st.error(f"Erro {resp.status_code} na Fal.ai: {resp.text}")
                            break
                        data = resp.json()
                        img_url = data["images"][0]["url"]
                        img_bytes = urllib.request.urlopen(img_url).read()
                        imgs_geradas.append((f"{prefixo}_{i+1:02d}.jpg", img_bytes))
                    except Exception as e:
                        st.error(f"Erro na capa {i+1}: {e}")
                        break
                        
                barra.progress(1.0, text="Lote concluído!")
                if imgs_geradas:
                    st.session_state["lote_capas_bytes"] = imgs_geradas
                    st.session_state["lote_prefixo"] = prefixo
                    
        if st.session_state.get("lote_capas_bytes"):
            lote = st.session_state["lote_capas_bytes"]
            pref_salvo = st.session_state.get("lote_prefixo", "capa_astronauta")
            st.success(f"{len(lote)} capas geradas em formato 16:9!")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for nome_arq, conteudo in lote:
                    zf.writestr(nome_arq, conteudo)
                    
            st.download_button(
                f"Baixar Todas as {len(lote)} Capas (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{pref_salvo}_lote_{len(lote)}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
            
            cols = st.columns(3)
            for idx, (nome_arq, conteudo) in enumerate(lote):
                cols[idx % 3].image(conteudo, caption=nome_arq, use_container_width=True)

    with tab_radar:
        st.markdown("#### Radar de Capas Concorrentes & Engenharia Reversa")
        st.caption("Puxe as thumbnails mais vistas do nicho no YouTube e use o Gemini Vision para dissecar a composição.")
        
        c_r1, c_r2 = st.columns([3, 1])
        termo_radar = c_r1.text_input("Nicho ou Palavra-Chave no YouTube", value="healing ambient music for anxiety")
        qtd_radar = c_r2.selectbox("Qtd de Vídeos", [6, 9, 12], index=1)
        
        buscar_radar_btn = st.button("Buscar Vídeos Mais Vistos", type="primary")
        
        yt_key = setting("YOUTUBE_API_KEY") or setting("YT_API_KEY")
        
        if buscar_radar_btn:
            if not valid_setting(yt_key):
                st.error("Chave YOUTUBE_API_KEY não configurada no secrets.toml.")
            else:
                try:
                    url_yt = "https://www.googleapis.com/youtube/v3/search"
                    params_yt = {
                        "part": "snippet",
                        "q": termo_radar,
                        "type": "video",
                        "order": "viewCount",
                        "maxResults": qtd_radar,
                        "key": yt_key
                    }
                    r_yt = requests.get(url_yt, params=params_yt, timeout=15)
                    data_yt = r_yt.json()
                    
                    if "items" in data_yt:
                        st.session_state["radar_thumbs"] = [
                            {
                                "id": it["id"]["videoId"],
                                "title": it["snippet"]["title"],
                                "channel": it["snippet"]["channelTitle"],
                                "thumb": f"https://i.ytimg.com/vi/{it['id']['videoId']}/hqdefault.jpg"
                            }
                            for it in data_yt["items"]
                        ]
                    else:
                        st.warning("Nenhum vídeo encontrado ou limite da API excedido.")
                except Exception as e_yt:
                    st.error(f"Erro ao consultar YouTube API: {e_yt}")
                    
        thumbs_encontradas = st.session_state.get("radar_thumbs", [])
        
        if thumbs_encontradas:
            st.divider()
            st.markdown(f"**Top referências para '{termo_radar}':**")
            
            cols_radar = st.columns(3)
            for idx, item in enumerate(thumbs_encontradas):
                with cols_radar[idx % 3]:
                    with st.container(border=True):
                        st.image(item["thumb"], use_container_width=True)
                        st.markdown(f"**{item['title'][:55]}...**")
                        st.caption(f"📺 {item['channel']}")
                        if st.button("Analisar com Gemini", key=f"btn_analisar_{item['id']}", use_container_width=True, type="primary"):
                            st.session_state["thumb_selecionada"] = item
                        
        if st.session_state.get("thumb_selecionada"):
            item_sel = st.session_state["thumb_selecionada"]
            st.divider()
            st.markdown(f"### Análise de Engenharia Reversa: *{item_sel['title']}*")
            
            col_preview, col_laudo = st.columns([1, 2])
            with col_preview:
                st.image(item_sel["thumb"], caption="Thumbnail de Referência", use_container_width=True)
                
            with col_laudo:
                gemini_key = setting("GEMINI_API_KEY")
                if not valid_setting(gemini_key):
                    st.error("Chave GEMINI_API_KEY não configurada no secrets.toml.")
                else:
                    with st.spinner("Dissecando a imagem (resposta rápida em ~5s)..."):
                        try:
                            req_img = urllib.request.Request(item_sel["thumb"], headers={"User-Agent": "Mozilla/5.0"})
                            raw_img = urllib.request.urlopen(req_img).read()
                            img_b64 = base64.b64encode(raw_img).decode("utf-8")
                            
                            prompt_instrucao = (
                                "Você é um diretor de arte sênior de thumbnails do YouTube. "
                                "Analise a imagem enviada e forneça de forma direta e organizada:\n"
                                "1. Paleta de Cores e Iluminação.\n"
                                "2. Elementos de Composição.\n"
                                "3. Psicologia do Clique (por que atrai cliques nesse subnicho).\n"
                                "4. Prompt Pronto para o FLUX (em inglês, formato 16:9, recriando a estética desta capa)."
                            )
                            
                            modelos_tentativa = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
                            sucesso = False
                            ultimo_erro = ""
                            
                            for mod in modelos_tentativa:
                                url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
                                payload_gemini = {
                                    "contents": [{
                                        "parts": [
                                            {"text": prompt_instrucao},
                                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                                        ]
                                    }],
                                    "generationConfig": {
                                        "thinkingConfig": {"thinkingBudget": 0}
                                    }
                                }
                                
                                res_g = requests.post(url_gemini, json=payload_gemini, timeout=35)
                                if res_g.status_code == 200:
                                    resp_text = res_g.json()["candidates"][0]["content"]["parts"][0]["text"]
                                    st.markdown(resp_text)
                                    sucesso = True
                                    break
                                elif res_g.status_code == 400:
                                    del payload_gemini["generationConfig"]
                                    res_g2 = requests.post(url_gemini, json=payload_gemini, timeout=35)
                                    if res_g2.status_code == 200:
                                        resp_text = res_g2.json()["candidates"][0]["content"]["parts"][0]["text"]
                                        st.markdown(resp_text)
                                        sucesso = True
                                        break
                                    ultimo_erro = f"{res_g2.status_code} - {res_g2.text}"
                                else:
                                    ultimo_erro = f"{res_g.status_code} - {res_g.text}"
                                    
                            if not sucesso:
                                st.error(f"Erro na API do Gemini: {ultimo_erro}")
                        except Exception as e_gem:
                            st.error(f"Falha na análise: {e_gem}")

elif page == "Espião & Ferramentas":
    page_header("Espião de Concorrentes & Utilidades", "Analise vídeos campeões de qualquer canal, simule ganhos de AdSense e gerencie seus projetos.")
    t_spy, t_vids, t_sim, t_proj, t_cfg = st.tabs([
        "Channel Spy",
        "Pesquisa de Vídeos",
        "Simulador AdSense",
        "Meus Projetos",
        "Chave da API"
    ])
    
    with t_spy:
        ref = st.text_input("Link do canal, ID UC... ou @usuario", "@YouTube")
        if st.button("Analisar canal concorrente", type="primary"):
            ch = demo_channels()[0] if demo else get_channel(ref, API_KEY)
            vids = demo_videos(ch["channel_id"]) if demo else latest_channel_videos(ch, API_KEY, 30)
            show_videos(vids, outliers=True)
            
    with t_vids:
        q = st.text_input("Termo de Pesquisa Avulsa", "ambient music for lonely nights")
        if st.button("Pesquisar vídeos", type="primary"):
            st.session_state["video_results"] = demo_videos() if demo else search_videos(q, API_KEY, "viewCount", 30)
        if st.session_state.get("video_results"):
            show_videos(st.session_state["video_results"], outliers=True)
            
    with t_sim:
        v = st.number_input("Visualizações mensais estimadas", value=100000, step=10000)
        low, high = revenue_range(v, 0.8, 2.5)
        st.metric("Estimativa Mensal de AdSense (USD)", f"${low:,.2f} a ${high:,.2f}")
        
    with t_proj:
        projetos_salvos = store.projects()
        if not projetos_salvos:
            st.info("Nenhum projeto salvo ainda.")
        for p in projetos_salvos:
            panel(p["name"], f"{p.get('niche','')} · {p.get('status','')}", p.get("notes", ""))
            
    with t_cfg:
        ck = st.text_input("Substituir YouTube API Key temporariamente", type="password")
        if st.button("Salvar Chave", type="primary"):
            st.session_state["custom_api_key"] = ck.strip()
            st.rerun()


"""Rebecca Studio V6 — Modular (3 Abas)"""
import base64
import io
import json
import os
import re
import requests
import streamlit as st
from PIL import Image

SYSTEM_INSTRUCTIONS = """INSTRUÇÕES DO SISTEMA — AGENTE GERADOR DE PROMPTS JSON
REBECCA LINS V1.3 — CEDAR DREAM

1. SUA FUNÇÃO E MISSÃO
Você é um Engenheiro de Prompts especializado em visão computacional e fotografia ultrarrealista.
Sua função é receber uma imagem de referência e traduzir precisamente sua composição, pose, ambiente e iluminação para o Template JSON. A personagem deve ser SEMPRE Rebecca Lins. Preserve a estética da fotografia original sem incorporar a identidade da pessoa fotografada.

2. DNA CANÔNICO IMUTÁVEL
Identidade Facial: Brasileira adulta (~25 anos), latina/mediterrânea. Rosto oval, maçãs altas, lábios volumosos, olhos castanhos amendoados.
Descrição Corporal: Cabelos longos castanho-escuros ondulados. Pele bronzeada dourado-oliva com poros visíveis. Corpo esguio, levemente atlético. Busto e glúteos moderados naturais. Pinta na bochecha direita. Piercing discreto no umbigo. Sem tatuagens.

3. REGRAS
EXTRAIR: Pose corporal, cenário, iluminação, perspectiva óptica.
IGNORAR: Identidade facial e corporal da referência original.

4. TEMPLATE OBRIGATÓRIO (retorne apenas o JSON puro):
{
  "meta": {"aspect_ratio": "4:5", "quality": "ultra_photorealistic", "resolution": "high_resolution", "camera": "...", "lens": "...", "style": "..."},
  "cena": {"local": "...", "ambiente": ["..."], "atmosfera": "..."},
  "iluminacao": {"tipo": "...", "luz_principal": "...", "luz_de_preenchimento": "...", "contraste": "...", "evitar": ["pele plástica"]},
  "perspectiva_da_camera": {"pov": "...", "angulo": "...", "distancia": "...", "visibilidade_do_celular": "..."},
  "assunto": {
    "vibe": "...", "textura_pele": "...", 
    "expressao": {"olhos": "...", "boca": "...", "emocao": "..."}, 
    "pose": {"posicao": "...", "apoio": "...", "mao": "..."},
    "roupa": {"blusa": {"tipo": "...", "caimento": "...", "detalhes": "..."}, "extra": ["..."]}
  },
  "qualidade_da_imagem": {"foco": "...", "granulacao": "...", "nitidez": "...", "realismo": "...", "pos_processamento": "..."}
}"""

AUDIT_PROMPT = """Você é um Auditor Rigoroso de Realismo de IA.
Analise a imagem e retorne APENAS um JSON:
{
  "nota_realismo": 88,
  "veredito": "APROVADA PARA FEED (ou REPROVADA)",
  "analise_pele_luz": "Avalie poros e coerência de luz.",
  "fidelidade_rebecca": "Avalie traços latinos, pinta e proporções.",
  "bugs_encontrados": ["Liste erros anatômicos"],
  "legenda_instagram_pt": "Sugestão de legenda."
}"""

def file_to_data_uri(file_bytes: bytes, mime_type: str) -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"

def compile_json_to_natural_prompt(data: dict) -> str:
    meta = data.get("meta", {})
    cena = data.get("cena", {})
    ilum = data.get("iluminacao", {})
    cam = data.get("perspectiva_da_camera", {})
    assunto = data.get("assunto", {})
    exp = assunto.get("expressao", {})
    pose = assunto.get("pose", {})
    roupa = assunto.get("roupa", {})
    blusa = roupa.get("blusa", {})
    qual = data.get("qualidade_da_imagem", {})

    ambiente_str = ", ".join(cena.get("ambiente", []))
    extras_str = ", ".join(roupa.get("extra", []))

    return (
        f"Ultra-photorealistic candid photography. {meta.get('camera', '')}, {meta.get('lens', '')}, {meta.get('style', '')}. "
        "Rebecca Lins, a 25-year-old Brazilian woman with warm olive-tanned skin, realistic human skin microtexture with subtle visible pores, "
        "long dark brown wavy hair, a small dark beauty mark on her right cheek near the nose base, slim toned curvy body, "
        "flat toned stomach, natural moderate bust, moderate rounded glutes, and a discreet navel piercing with two small metal spheres when stomach is visible. "
        f"Pose & Action: {pose.get('posicao', '')}, {pose.get('apoio', '')}, {pose.get('mao', '')}. "
        f"Expression: {exp.get('olhos', '')}, {exp.get('boca', '')}, {exp.get('emocao', '')}, vibe: {assunto.get('vibe', '')}. "
        f"Outfit: {blusa.get('tipo', '')} ({blusa.get('detalhes', '')}, {blusa.get('caimento', '')}), {extras_str}. "
        f"Setting: {cena.get('local', '')}, {ambiente_str}. Atmosphere: {cena.get('atmosfera', '')}. "
        f"Camera perspective: {cam.get('pov', '')}, {cam.get('angulo', '')}, {cam.get('distancia', '')}, phone visibility: {cam.get('visibilidade_do_celular', '')}. "
        f"Lighting: {ilum.get('tipo', '')}, {ilum.get('luz_principal', '')}, {ilum.get('luz_de_preenchimento', '')}. "
        f"Quality: {qual.get('foco', '')}, {qual.get('nitidez', '')}, {qual.get('pos_processamento', '')}."
    )

def call_gemini_vision(api_key: str, image_bytes: bytes, mime_type: str, system_prompt: str) -> dict:
    clean_key = str(api_key or "").strip().replace(" ", "").replace("\n", "").replace("\r", "")
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85)
        image_bytes = out_buf.getvalue()
        mime_type = "image/jpeg"
    except Exception:
        pass

    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"inlineData": {"mimeType": mime_type, "data": b64_img}}, {"text": "Analise a imagem e retorne exclusivamente o JSON preenchido."}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    
    headers = {"Content-Type": "application/json"}
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]
    
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
        r_list = requests.get(list_url, timeout=10)
        if r_list.status_code == 200:
            avail = [
                m["name"].replace("models/", "") for m in r_list.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", []) and "1.5" not in m["name"] and "tts" not in m["name"] and "image" not in m["name"]
            ]
            flash_models = [m for m in avail if "flash" in m and "lite" not in m]
            pro_models = [m for m in avail if "pro" in m]
            if flash_models or pro_models:
                candidate_models = flash_models + pro_models
    except Exception:
        pass

    erros = []
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        try:
            # Timeout estendido para 180s para evitar o Read timed out
            resp = requests.post(url, headers=headers, json=payload, timeout=180)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()
                start_idx = clean_text.find("{")
                if start_idx != -1:
                    clean_text = clean_text[start_idx:]
                
                decoder = json.JSONDecoder()
                parsed_json, _ = decoder.raw_decode(clean_text)
                return parsed_json
                
            erros.append(f"{model_name} -> {resp.status_code}")
            if resp.status_code in (404, 429, 400, 503):
                continue
        except requests.exceptions.Timeout:
            erros.append(f"{model_name} -> Timeout (180s)")
            continue

    raise RuntimeError(f"Falha ao extrair. Tentativas: {', '.join(erros)}")

def render_rebecca_studio(gemini_key: str = "", fal_key: str = ""):
    st.markdown('<div class="eyebrow">REBECCA LINS • AI INFLUENCER SUITE V6</div>', unsafe_allow_html=True)
    st.title("Rebecca Studio — Estúdio Modular")

    with st.expander("🔑 Configurar Chaves de API", expanded=True):
        c1, c2 = st.columns(2)
        g_in = c1.text_input("Gemini API Key", value=gemini_key or os.getenv("GEMINI_API_KEY", ""), type="password")
        f_in = c2.text_input("Fal.ai API Key", value=fal_key or os.getenv("FAL_KEY", ""), type="password")
        st.session_state["gemini_key_v6"] = g_in.strip()
        st.session_state["fal_key_v6"] = f_in.strip()

    active_gemini = st.session_state.get("gemini_key_v6", "")
    active_fal = st.session_state.get("fal_key_v6", "")

    view_mode = st.radio(
        "Módulos",
        ["1. Extração de Prompts (Gemini)", "2. Gerador Fal.ai (Face Lock)", "3. Auditor de Qualidade"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

    if view_mode == "1. Extração de Prompts (Gemini)":
        st.subheader("Extrair JSON e Prompt da Referência")
        pose_files = st.file_uploader("Suba fotos (Pinterest/Instagram)", type=["jpg", "png", "webp"], accept_multiple_files=True)
        
        if pose_files and st.button("🚀 Extrair Dados", type="primary"):
            if not active_gemini:
                st.error("Insira a chave do Gemini.")
                return
            
            for idx, p_file in enumerate(pose_files):
                st.divider()
                st.markdown(f"**Referência:** {p_file.name}")
                c_img, c_code = st.columns([1, 2])
                c_img.image(p_file.getvalue(), use_container_width=True)
                
                with c_code:
                    with st.spinner("Analisando com Gemini (Pode levar até 1 minuto)..."):
                        try:
                            json_data = call_gemini_vision(active_gemini, p_file.getvalue(), p_file.type or "image/jpeg", SYSTEM_INSTRUCTIONS)
                            en_prompt = compile_json_to_natural_prompt(json_data)
                            st.session_state[f"prompt_cache_{idx}"] = en_prompt
                            
                            st.success("Extração Concluída!")
                            st.text_area("Prompt em Inglês (Copie para a Aba 2)", en_prompt, height=150)
                            with st.expander("Ver JSON Completo"):
                                st.json(json_data)
                        except Exception as e:
                            st.error(f"Erro: {e}")

    elif view_mode == "2. Gerador Fal.ai (Face Lock)":
        st.subheader("Gerar Imagem na Nuvem")
        
        c_mod1, c_mod2, c_mod3 = st.columns(3)
        model_choice = c_mod1.selectbox("Modelo", ["fal-ai/flux-pulid (Face Lock)", "fal-ai/flux-pro/v1.1-ultra", "fal-ai/flux/schnell (Teste)"])
        aspect_ratio = c_mod2.selectbox("Proporção", ["4:5", "9:16", "1:1"])
        num_images = c_mod3.number_input("Quantas imagens gerar?", min_value=1, max_value=30, value=1)
        
        face_anchor_file = st.file_uploader("Imagem Âncora de Rosto (Obrigatório para PuLID)", type=["jpg", "png"])
        
        # Puxa o prompt em cache da Aba 1, se existir
        cached_prompt = st.session_state.get("prompt_cache_0", "")
        prompt_to_run = st.text_area("Cole o Prompt em Inglês aqui", value=cached_prompt, height=150)

        if st.button("🎨 Gerar Imagem", type="primary", use_container_width=True):
            if not active_fal:
                st.error("Insira a chave da Fal.ai.")
                return
            if not prompt_to_run.strip():
                st.error("O campo do prompt está vazio.")
                return
            if "pulid" in model_choice and not face_anchor_file:
                st.error("Para usar o Face Lock (PuLID), suba a foto âncora do rosto.")
                return
                
            with st.spinner(f"Gerando {num_images} imagem(ns)..."):
                headers = {"Authorization": f"Key {active_fal}", "Content-Type": "application/json"}
                dimensions = {"4:5": {"width": 896, "height": 1152}, "9:16": {"width": 768, "height": 1344}, "1:1": {"width": 1024, "height": 1024}}[aspect_ratio]
                
                anchor_uri = file_to_data_uri(face_anchor_file.getvalue(), face_anchor_file.type or "image/jpeg") if face_anchor_file else None

                if "pulid" in model_choice:
                    endpoint = "https://fal.run/fal-ai/flux-pulid"
                    payload = {"prompt": prompt_to_run, "reference_image_url": anchor_uri, "image_size": dimensions, "num_inference_steps": 28, "guidance_scale": 3.5, "id_weight": 0.85, "num_images": num_images}
                elif "schnell" in model_choice:
                    endpoint = "https://fal.run/fal-ai/flux/schnell"
                    payload = {"prompt": prompt_to_run, "image_size": dimensions, "num_images": num_images}
                else:
                    endpoint = "https://fal.run/fal-ai/flux-pro/v1.1-ultra"
                    payload = {"prompt": prompt_to_run, "aspect_ratio": aspect_ratio, "num_images": num_images}

                try:
                    r = requests.post(endpoint, headers=headers, json=payload, timeout=180)
                    r.raise_for_status()
                    images = r.json().get("images", [])
                    
                    cols = st.columns(min(len(images), 3) if images else 1)
                    for i, img_data in enumerate(images):
                        with cols[i % 3]:
                            st.image(img_data["url"], use_container_width=True)
                            st.markdown(f"[Baixar #{i+1}]({img_data['url']})")
                except Exception as e:
                    st.error(f"Erro na geração: {e}")

    elif view_mode == "3. Auditor de Qualidade":
        st.subheader("Auditor de Realismo")
        audit_file = st.file_uploader("Suba a foto final gerada", type=["jpg", "png"])
        if audit_file and st.button("🔍 Auditar", type="primary"):
            if not active_gemini:
                st.error("Chave Gemini ausente.")
            else:
                with st.spinner("Analisando..."):
                    try:
                        rep = call_gemini_vision(active_gemini, audit_file.getvalue(), audit_file.type or "image/jpeg", AUDIT_PROMPT)
                        st.metric("Realismo", f"{rep.get('nota_realismo', 0)}/100")
                        st.markdown(f"**Pele/Luz:** {rep.get('analise_pele_luz', '')}")
                        st.markdown(f"**Fidelidade:** {rep.get('fidelidade_rebecca', '')}")
                        st.code(rep.get("legenda_instagram_pt", ""))
                    except Exception as e:
                        st.error(f"Erro na auditoria: {e}")

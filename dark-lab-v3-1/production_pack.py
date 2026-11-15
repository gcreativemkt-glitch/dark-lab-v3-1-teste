"""Exporta relatórios e roteiros com proveniência explícita, sem credenciais."""
from __future__ import annotations
import io
import json
import zipfile
from datetime import datetime, timezone


def make_production_zip(query, report, plans):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w', zipfile.ZIP_DEFLATED) as z:
        manifest = {
            'project': 'Dark Lab — piloto editorial',
            'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'niche': query,
            'research': report,
            'warning': 'Análise amostral. Não prova renda, monetização, busca total nem concorrência baixa.',
            'plan': plans,
        }
        z.writestr('01_RELATORIO_E_PLANO.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        lines = [
            f'# DARK LAB — {query}', '',
            f"Situação: {report['status']}",
            f"Confiança: {report['confidence']}",
            f"Amostra: {report['sample_size']} vídeos de {report['channels']} canais",
            f"Mediana de visualizações/dia desde a publicação: {report['median_vpd_lifetime']}",
            f"Canais jovens com vídeo em destaque na amostra: {report['young_breakout_channels']}",
            f"Parcela das visualizações concentrada nos três maiores canais da amostra: {report['top3_views_share']}%",
            '', '## LIMITAÇÕES',
            'Esses indicadores não medem buscas totais, mercado inteiro, faturamento nem elegibilidade para anúncios.',
            'O ranking é indicativo e precisa ser confrontado com amostra, direitos e execução.',
            '', '## ALERTAS', *['- ' + n for n in report['notes']],
            '', '## REFERÊNCIAS DO YOUTUBE',
        ]
        for r in report['references']:
            lines.append(f"- {r['title']} — {r['channel']} — {r['url']}")
        z.writestr('00_LEIA_PRIMEIRO.md', '\n'.join(lines))
        for p in plans:
            head = [
                f"# VÍDEO {p['video']:02d} — {p['title']}", '',
                f"Conceito: {p['concept']}",
                f"Duração-alvo: {p['target_duration_minutes']} minutos (confirmar depois da montagem)",
                f"Faixas previstas: {p['target_tracks']} composições distintas", '',
                '## ESTILO MUSICAL', p['music_style'], '',
                '## CAPA 16:9', p['cover_prompt'],
                'Negativos da capa: ' + p['negative_visual_prompt'], '',
                '## DESCRIÇÃO RASCUNHO', p['description'], '',
                '## PROMPTS SUNO — UMA MÚSICA DIFERENTE POR ITEM',
            ]
            for t in p['tracks']:
                head.extend(['', f"### {t['track']}", 'Style: ' + t['style'], 'Exclude: ' + t['negative'], t['note']])
            head.extend(['', '## VERIFICAÇÃO PRÉ-PUBLICAÇÃO',
                         '- Confirmar os direitos das músicas utilizadas',
                         '- Verificar duração do vídeo e corrigir o título',
                         '- Ajustar descrição e capítulos aos arquivos finais',
                         '- Confirmar originalidade do compilado e da capa',
                         '- Revisar referências antes de publicar'])
            z.writestr(f"video_{p['video']:02d}/BRIEFING_E_PROMPTS.md", '\n'.join(head))
    return payload.getvalue()

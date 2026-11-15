# 🌙 Dark Lab V3.1 — Revisão de segurança, Radar e planejamento

Aplicativo pessoal **Streamlit + YouTube Data API**, derivado da versão V3 enviada pelo usuário. Esta é uma **proposta de atualização, para testar antes de substituir a versão de produção**. A interface dark foi preservada; algumas funcionalidades não relacionadas ao YouTube foram retiradas da navegação.

## Mudanças principais

1. **Scanner baseado em duas amostras por termo:** até 25 vídeos populares + 25 publicados recentemente, com remoção de vídeos duplicados e dados dos canais associados.
2. **Oceano Azul com prudência:** avalia canais jovens com vídeos fortes, tração histórica, concentração das visualizações e confiança. Não usa mais o índice de "saturação real" da V3 como se medisse todos os concorrentes.
3. **Histórico opcional:** salva visualizações por vídeo/dia em SQLite ou Supabase. **Só após uma coleta em outro dia** poderá calcular crescimento observado; dividir visualizações por idade é uma média histórica, não crescimento recente.
4. **Mesmo relatório no Scanner e no Copiloto:** elimina decisões conflitantes vindas de amostras separadas no fluxo principal.
5. **Planejador com dados reais:** não permite criar lotes a partir de `demo_videos()` ou de um nicho diferente do relatório selecionado. Primeiro faz a pesquisa, depois envia a mesma evidência para o Planejador.
6. **Pacote ZIP com 2 a 6 vídeos:** inclui referências, análise e briefings individuais com títulos, duração-alvo, prompts Suno de faixas distintas, prompts negativos, capa 16:9, descrição preliminar e lista de verificações.
7. **Segurança:** removido login compartilhado globalmente e token de autenticação persistido na URL. Senha passa a valer por sessão por até 24 horas; APP_PASSWORD é obrigatório quando existem integrações pagas configuradas.
8. **Escopo simplificado:** Rebecca Studio continua preservado no arquivo separado `rebecca_studio.py`, mas não aparece no menu do projeto YouTube. Removido o embaralhador de músicas, que incentivava compilados com material muito repetido.

## O que o programa NÃO promete

- Não consegue saber a receita de concorrentes nem comprovar aprovação de canais no Programa de Parcerias do YouTube.
- Não conhece o volume exato de buscas ou a concorrência total de um nicho; o **índice é apenas uma triagem amostral**.
- Não analisa o áudio de vídeos concorrentes: os estilos criativos ainda são gerados a partir de termos e presets editoriais, **não por uma IA generativa examinando as músicas**.
- Não cria músicas no Suno nem envia vídeos automaticamente ao YouTube.
- Não confirma a qualidade ou elegibilidade de uma composição, faixa ou compilado para monetização.

## Como testar sem perder a versão atual

1. Preserve um ZIP e, se possível, uma branch/cópia do repositório atual.
2. Coloque esta versão **em uma branch de testes** ou em outro repositório privado, antes de mexer na aplicação publicada.
3. Se utilizar Supabase, execute o arquivo `supabase.sql` no SQL Editor. O comando adiciona `video_snapshots` sem excluir as tabelas anteriores. Sem atualizar, a análise continua funcionando, mas o histórico de crescimento não será salvo.
4. Configure **Secrets** no Streamlit Community Cloud (nunca no GitHub) usando `.streamlit/secrets.toml.example` como referência:

   ```toml
   APP_PASSWORD = "SENHA_FORTE_EXCLUSIVA"
   YOUTUBE_API_KEY = "SUA_CHAVE"
   # SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
   # SUPABASE_SERVICE_KEY = "SUA_CHAVE_PRIVADA"
   # FAL_API_KEY = "SUA_CHAVE_FAL"
   # GEMINI_API_KEY = "SUA_CHAVE_GEMINI"
   ```

5. Deploy pelo Streamlit Community Cloud apontando para `app.py`; mantenha a senha habilitada.
6. Abra o **Scanner de Nichos**, desative **Modo demonstração** se houver chave configurada, clique em **Encontrar oportunidades** e leia confiança e referências.
7. Escolha um nicho, clique em **Criar pacote de produção**, abra **Planejador & Suno** e baixe o ZIP.
8. Para verificar crescimento observado, repita a pesquisa **em outro dia** com o mesmo termo e armazenamento persistente.

## Rodar localmente

Requer Python 3.11+ e acesso à internet para instalação de dependências.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Verificação automatizada

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

**Limitação importante:** o código foi compilado e as funções puras podem ser testadas localmente, mas ainda requer um teste real de interface no Streamlit e chamadas de API com suas credenciais. Não publique substituindo a única versão sem criar backup/branch.

## Organização

- `app.py` — interface principal
- `opportunity_engine.py` — relatórios exploratórios e criação editorial
- `production_pack.py` — ZIP de pesquisa e produção
- `youtube_api.py` — consultas à API oficial
- `storage.py` e `supabase.sql` — dados locais/remotos e histórico de crescimento
- `analytics.py` — compatibilidade e outras métricas legadas; **não use as antigas classificações de saturação para decisões**
- `rebecca_studio.py` — módulo legado guardado para eventual uso separado
- `.gitignore` — exclusão de credenciais e arquivos locais
- `tests/` — testes unitários e de regressão

## Próxima melhoria candidata

Conectar IA generativa ao pacote editorial, usando **somente o relatório salvo como evidência** e distinguindo claramente observação factual de sugestão criativa. Não considerar essa etapa pronta na V3.1.

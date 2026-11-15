# Auditoria técnica — Dark Lab (15/11/2026)

## Escopo

Revisão estática do ZIP `dark-lab-main.zip` enviado nesta conversa; comparação entre a implementação V3 original e uma proposta V3.1. Não foram usadas credenciais reais. A interface e as chamadas reais ao YouTube/Fal.ai/Gemini NÃO foram executadas no ambiente de auditoria.

## Questões verificadas na V3 original

1. **Autenticação aberta entre sessões:** `daily_auth_store()` em `@st.cache_resource` mantinha a opção `locked=False` comum às sessões, e a senha diária poderia ser substituída por token determinístico de URL. Após uma autenticação, outro cliente poderia ser liberado sem digitar senha. Corrigido na proposta com estado somente por sessão e sem token de URL.
2. **Sem consistência entre abas:** Scanner baseava-se em `search_videos` com até 25 vídeos por nicho; o Copiloto fazia outra pesquisa separada, e o Planejador usava qualquer `planner_sample` ou `radar_sample` salvo. Corrigido no fluxo principal, que compartilha relatório e vídeo amostral entre Scanner e Planejador.
3. **Fallback demonstrativo perigoso:** o Planejador utilizava `demo_videos()` na ausência de amostra. Corrigido: requer pesquisa não demonstrativa, evidência mínima e associação ao mesmo nicho.
4. **"Saturação" não é concorrência real:** `analytics.niche_summary` calculava a fórmula a partir de diversidade, proporção recente e outlier do conjunto, mas rotulava como saturação e "Oceano Azul". Substituído na tela principal por evidências da amostra e índices explicitamente exploratórios.
5. **"Views/dia" não é velocidade observada:** era `views totais / idade em dias`. V3.1 separa média histórica do crescimento realmente observado em coletas de dias diferentes.
6. **Outlier misturado entre canais:** a mediana de um conjunto de vídeos de canais diferentes não é o outlier interno de cada canal. O indicador legado foi mantido em outras ferramentas, mas o rótulo agora informa quando é relativo à amostra. Cálculo específico de outlier ajustado por idade **ainda é etapa posterior**.
7. **Muitos vídeos automaticamente:** o Planejador preparava 15 a 100 entradas com uma música por entrada, muito pouco alinhadas com a produção de mixes musicais originais. Reduzido para lotes piloto de 2–6 vídeos e prompts para várias faixas distintas por vídeo.
8. **Risco de conteúdo repetitivo:** o embaralhador antigo gerava versões quase idênticas reorganizando músicas. Removido do menu nesta proposta; o arquivo original segue preservado no ZIP de origem.
9. **Mistura entre dois projetos:** `rebecca_studio.py` carregava no mesmo app e aparecia na navegação do Dark Lab. Retirado do menu; o arquivo foi preservado separadamente.
10. **Higiene de credenciais:** o ZIP inicial não continha `.gitignore`, embora o README dissesse que existia. Acrescentados `.gitignore` e `.streamlit/secrets.toml.example` sem chaves reais.

## O que mudou na V3.1

- `opportunity_engine.py`: analisa canais jovens, concentração de views, amostra e observações de crescimento; devolve status com confiança, notas e links.
- `youtube_api.py`: `scan_niche_two_views` combina duas ordenações (até 25 vídeos por ordem) por nicho, sem varrer tudo o que existe na plataforma.
- `storage.py` e `supabase.sql`: tabela `video_snapshots` para comparação entre coletas de dias diferentes.
- `app.py`: fluxo Scanner → relatório salvo → Planejador → ZIP, sem dados de demonstração como pesquisa real.
- `production_pack.py`: exporta relatório com referências e briefings por vídeo/por faixa.
- `tests/test_opportunity.py`, `tests/test_snapshots.py`: testes sobre falsos positivos, amostra insuficiente, crescimento observado, ZIP e persistência.
- Autenticação alterada para sessão independente; nenhum token de acesso fica na URL.

## Limitações e próximos passos

- Índices ainda são **heurísticos**; não existe método público confiável para verificar a receita ou a concorrência total de cada micronicho via YouTube Data API.
- O pacote musical usa regras e presets a partir do termo pesquisado, não análise de áudio por IA. Se vier a ser integrado ao Gemini, a análise generativa deve trabalhar apenas sobre o relatório salvo e marcar claramente as sugestões não verificadas.
- A API pode consumir cota mais rapidamente porque são duas buscas por nicho. Consulte quota do seu projeto, use o cache e evite varreduras repetidas sem necessidade.
- Crescimento observado só fica disponível em coletas de **dias diferentes** e com base de dados persistente.
- Não há automação de postagem; a postagem manual continua como escolha do proprietário.
- O projeto necessita verificação funcional no Streamlit e nas credenciais oficiais antes do uso real.
- O Radar não confirma se canal de música já monetiza ou se uma composição gerada dá direito autoral ou licença adequada para uso; revisar termos do Suno e políticas atuais do YouTube separadamente.

## Verificações realizadas

- `python -m compileall -q .`: código Python compilou sem erros de sintaxe.
- `python -m unittest discover -s tests -v`: 13 testes passaram.
- Simulação local com amostra sintética: relatório com referências e dois briefings exportados corretamente em ZIP.
- Não houve teste interativo com Streamlit instalado, nem acesso à API do YouTube, Supabase, Fal.ai ou Gemini.

## Procedimento recomendado de implantação

1. **Não substitua a única versão atual.** Preserve o ZIP original, crie uma branch `teste-darklab-v31` ou novo repositório privado de testes.
2. Faça upload dos arquivos **extraídos** desta versão para a branch de testes. Não envie `.env`, `secrets.toml` ou diretórios `data/`.
3. Se usa Supabase, abra o SQL Editor e execute o conteúdo de `supabase.sql` (cria tabela adicional, sem excluir as antigas).
4. Crie uma aplicação secundária no Streamlit Community Cloud apontando para a branch de testes e o mesmo `app.py`. Insira Secrets apenas nas configurações privadas da aplicação, com `APP_PASSWORD` forte.
5. Confirme a tela de senha em janela anônima **antes** de usar API paga ou service key.
6. Verifique `Modo demonstração` desligado. Faça um Scanner real. O ranking deve mostrar origem, evidências e advertências, não faturamento ou saturação literal.
7. Entre no Plano de Produção e baixe o ZIP. Confira se títulos, prompts e nicho correspondem à mesma varredura. Verifique links de vídeo.
8. Repita o scanner em outra data para testar o crescimento observado. Publique vídeo somente após rever direitos de músicas e qualidade editorial.
9. Somente após esses testes, considere mesclar a branch e atualizar a aplicação de produção.

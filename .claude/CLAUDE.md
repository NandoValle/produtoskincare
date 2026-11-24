# produtoskincare.com.br

- **Todo post novo do blog sai com capa** (foto 16:9 ultrarrealista gerada no ChatGPT). Post sem capa está incompleto. O passo a passo, o estilo fixo do prompt e as regras da cena estão em `_roteiros/capas.txt`; o script é `_scripts/capa_post.py`.
- Página nova ou alterada: rodar `python -I _scripts/seo.py` depois.
- Por último, depois de qualquer gerador e do `seo.py`: rodar `python -I _scripts/prontidao.py`. Ele devolve às páginas o bloco WebMCP do `<head>`, as perguntas frequentes de `_scripts/perguntas.json`, a linha de atualização e o tamanho de título e descrição. Os `gerar_*.py` reescrevem a página inteira e apagam isso. Página nova de conteúdo: acrescentar 2 perguntas dela em `perguntas.json`, respondidas só com o que a página diz.
- Post novo ou alterado no blog: rodar `python -I _scripts/gerar_feed.py` para atualizar o `blog/feed.xml` (RSS). Ele lê os cartões de `blog/index.html`; o post precisa estar lá.
- Ficha de ativo nova ou alterada (`/ativos/<slug>/` ou `/ingredientes/<slug>/`): rodar `python -I _scripts/decisao_ficha.py`. Ele abre a ficha com as quatro respostas de decisão (por que considerar, quando pular, em que etapa entra, o que sabemos), montadas só com o que a ficha já diz, e tira link de busca de loja: sem oferta conferida, a ficha não aponta onde comprar.
- Produto no catálogo: o botão de compra só aparece com link direto para o anúncio. Link de busca vira "sem oferta verificada". O tamanho conferido do frasco fica em `tamanho`, no `produtos.json`.

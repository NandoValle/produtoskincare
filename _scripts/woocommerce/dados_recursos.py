# Conteúdo das páginas do grupo "Recursos" da seção WooCommerce.
PAGINAS = [
    {
        "caminho": "/woocommerce/blog/", "rotulo": "Blog",
        "resumo": "Notícias, dicas de e-commerce e bastidores do ecossistema WooCommerce.",
        "titulo": "Blog do WooCommerce",
        "descricao": "O blog oficial do WooCommerce: notícias de produto, dicas de e-commerce, histórias de lojas e bastidores do ecossistema.",
        "lead": "O blog oficial reúne notícias de produto, dicas de venda, histórias de lojas que usam WooCommerce e o que muda em cada versão. É o ponto de partida para acompanhar o ecossistema.",
        "secoes": [
            ("O que publicam", "<p>Anúncios de versões, guias de venda (marketing, conversão, operação), estudos de caso e entrevistas com lojistas e agências. Há também o blog de desenvolvedores, para quem mexe com código.</p>"),
            ("Para quem é", "<p>Lojistas que querem vender melhor, agências que acompanham o ecossistema e desenvolvedores que precisam saber o que muda em cada release.</p>"),
        ],
        "cta": ("Ler o blog oficial", "https://woocommerce.com/blog/"),
        "faq": [
            ("O blog tem conteúdo em português?", "O blog oficial é majoritariamente em inglês. Comunidades e blogs parceiros publicam material em português."),
            ("Com que frequência atualiza?", "Publicações novas saem com frequência semanal, com mais volume perto de lançamentos de versão."),
        ],
    },
    {
        "caminho": "/woocommerce/documentacao/", "rotulo": "Documentação",
        "resumo": "Guias de instalação, configuração, extensões e solução de problemas.",
        "titulo": "Documentação do WooCommerce",
        "descricao": "Documentação oficial do WooCommerce: instalação, configuração de loja, produtos, pagamentos, envios, extensões e solução de problemas.",
        "lead": "A documentação oficial cobre o ciclo completo: instalar, configurar a loja, cadastrar produtos, ligar pagamentos e envios, usar extensões e resolver os problemas comuns.",
        "secoes": [
            ("Como navegar", "<p>Comece pelo guia de início rápido, siga para as seções de configuração (produtos, impostos, frete, e-mails) e use a busca quando travar. Quase todo erro de configuração já foi documentado por alguém.</p>"),
            ("Complementos", "<p>Além dos guias, há a referência para desenvolvedores, tutoriais por vídeo e os fóruns da comunidade para casos que a documentação não cobre.</p>"),
        ],
        "cta": ("Abrir a documentação", "https://woocommerce.com/documentation/"),
        "faq": [
            ("Tem guia de migração de outra plataforma?", "Sim: há documentação sobre importação de produtos e clientes por CSV e guias para migrações comuns."),
            ("E se a documentação não resolver?", "Use os fóruns da comunidade e, para produtos pagos, o canal de suporte do desenvolvedor."),
        ],
    },
    {
        "caminho": "/woocommerce/vitrine/", "rotulo": "Vitrine de clientes",
        "resumo": "Lojas reais construídas com WooCommerce, por segmento e porte.",
        "titulo": "Vitrine de clientes do WooCommerce",
        "descricao": "Estudos de caso e lojas reais construídas com WooCommerce: inspiração por segmento, porte e modelo de negócio.",
        "lead": "A vitrine reúne lojas reais construídas com WooCommerce — de marcas independentes a operações grandes — com estudos de caso que mostram o que cada escolha resolveu.",
        "secoes": [
            ("Para que serve", "<p>Antes de decidir arquitetura e fornecedores, ver como outros negócios parecidos resolveram dá referência concreta: estrutura de catálogo, checkout, integrações e resultados.</p>"),
            ("Como usar", "<p>Filtre por segmento e porte, leia o estudo de caso e observe o que é replicável no seu contexto — nem toda solução de loja grande cabe em loja pequena, e vice-versa.</p>"),
        ],
        "cta": ("Ver a vitrine", "https://woocommerce.com/showcase/"),
        "faq": [
            ("Posso enviar minha loja para a vitrine?", "O site oficial tem um canal de submissão de showcase — confira os critérios de seleção."),
            ("As lojas da vitrine são clientes pagos?", "A vitrine é editorial: reúne lojas consideradas referência, independente de contratos comerciais."),
        ],
    },
    {
        "caminho": "/woocommerce/atualizacoes/", "rotulo": "Atualizações de produto",
        "resumo": "O que muda em cada versão: recursos novos, correções e avisos.",
        "titulo": "Atualizações de produto do WooCommerce",
        "descricao": "Changelog e novidades de cada versão do WooCommerce: recursos novos, correções de segurança, mudanças de API e avisos para desenvolvedores.",
        "lead": "Cada versão do WooCommerce vem com notas de lançamento: o que mudou, o que foi corrigido, o que deprecou e o que afeta extensões. É a fonte oficial da verdade entre versões.",
        "secoes": [
            ("Como acompanhar", "<p>As notas de versão saem no blog e no changelog do repositório. Lojistas devem ler o resumo antes de atualizar; desenvolvedores, o changelog completo, com atenção a depreciações.</p>"),
            ("Rotina segura", "<p>Atualize em homologação primeiro, confira as extensões críticas, faça backup e só então publique em produção. É rotina simples que evita a maior parte das dores de cabeça.</p>"),
        ],
        "resumo_itens": [
            "Notas de versão oficiais a cada release.",
            "Depreciações avisam com antecedência para quem desenvolve.",
            "Backup e homologação antes de atualizar em produção.",
        ],
        "cta": ("Ver o changelog", "https://github.com/woocommerce/woocommerce/releases"),
        "faq": [
            ("Atualização quebra minhas extensões?", "Normalmente não, mas extensões sem manutenção podem conflitar. Teste em homologação e mantenha tudo atualizado."),
            ("Onde vejo avisos de segurança?", "No blog oficial e nas notas de versão; versões de correção de segurança saem fora do ciclo normal."),
        ],
    },
    {
        "caminho": "/woocommerce/newsletter/", "rotulo": "Newsletter por e-mail",
        "resumo": "Novidades, dicas e lançamentos do WooCommerce direto no seu e-mail.",
        "titulo": "Newsletter do WooCommerce",
        "descricao": "Assine a newsletter do WooCommerce: notícias de produto, dicas de e-commerce e lançamentos no seu e-mail.",
        "lead": "A newsletter oficial leva as notícias de produto, dicas de venda e lançamentos do ecossistema direto para o e-mail — sem precisar procurar.",
        "secoes": [
            ("O que chega", "<p>Resumos do que há de novo no WooCommerce, artigos de e-commerce, convites para webinars e eventos e destaques do Marketplace. Frequência moderada, com cancelamento fácil.</p>"),
            ("Dica de organização", "<p>Crie uma etiqueta ou caixa de entrada separada para newsletters de produto: vira um arquivo de consulta quando você precisar lembrar quando um recurso foi lançado.</p>"),
        ],
        "cta": ("Assinar a newsletter", "https://woocommerce.com/newsletter/"),
        "faq": [
            ("É pago?", "Não: a newsletter é gratuita e o cancelamento é pelo link no pé de cada e-mail."),
            ("Sai em português?", "O material oficial é majoritariamente em inglês — confira o idioma no formulário de inscrição."),
        ],
    },
    {
        "caminho": "/woocommerce/suporte/", "rotulo": "Suporte",
        "resumo": "Como obter ajuda: documentação, fóruns e suporte dos desenvolvedores.",
        "titulo": "Suporte do WooCommerce",
        "descricao": "Onde obter ajuda com WooCommerce: documentação, fóruns da comunidade, suporte dos desenvolvedores de extensões e hospedagem.",
        "lead": "Suporte no ecossistema WooCommerce vem em camadas: documentação para o comum, fóruns para a comunidade e canal direto com o desenvolvedor para extensões pagas.",
        "secoes": [
            ("Caminhos de ajuda", "<p>1) Documentação oficial; 2) fóruns da comunidade para dúvidas gerais; 3) suporte do desenvolvedor da extensão ou tema comprado; 4) suporte da hospedagem quando o problema é de servidor. Identificar a camada certa já resolve metade do caso.</p>"),
            ("Antes de pedir ajuda", "<p>Tenha em mãos: versões do WordPress e do WooCommerce, lista de extensões ativas, o que você tentou e a mensagem de erro exata. Um bom relato é respondido mais rápido.</p>"),
        ],
        "cta": ("Ver opções de suporte", "https://woocommerce.com/support/"),
        "faq": [
            ("O suporte do WooCommerce é pago?", "O núcleo é gratuito e o suporte da comunidade também. Produtos pagos têm suporte incluso, normalmente por um ano, renovável com a licença."),
            ("Onde abro chamado da minha extensão?", "No canal de suporte do desenvolvedor do produto — para itens do Marketplace, direto pela sua conta."),
        ],
    },
    {
        "caminho": "/woocommerce/pedidos-de-funcionalidade/", "rotulo": "Solicitações de funcionalidade",
        "resumo": "Sugira recursos: o quadro de ideias do WooCommerce e como votar.",
        "titulo": "Solicitações de funcionalidade do WooCommerce",
        "descricao": "Sugira e vote em recursos para o WooCommerce: o quadro de ideias oficial, o fluxo de triagem e como acompanhar pedidos.",
        "lead": "O WooCommerce mantém um quadro aberto de ideias: qualquer pessoa sugere recursos e vota nos pedidos. A demanda real de usuários orienta o roadmap.",
        "secoes": [
            ("Como funciona", "<p>Antes de abrir pedido novo, procure se a ideia já existe — somar votos vale mais que duplicar. Descreva o problema antes da solução: times de produto decidem com base no caso de uso, não na feature pedida.</p>"),
            ("E depois", "<p>Pedidos populares entram em avaliação; quando viram roadmap, há comunicação no blog e nas notas de versão. Nem toda sugestão vira recurso, e extensões resolvem muita coisa no meio-tempo.</p>"),
        ],
        "cta": ("Abrir o quadro de ideias", "https://woocommerce.com/feature-requests/"),
        "faq": [
            ("Votar garante que o recurso sai?", "Não: votos mostram demanda, mas priorização depende de estratégia, esforço e impacto."),
            ("Posso pedir recurso para uma extensão?", "Pedidos de extensões de terceiros vão para o desenvolvedor do produto, não para o núcleo."),
        ],
    },
    {
        "caminho": "/woocommerce/hospedagem/", "rotulo": "Hospedagem no WooCommerce",
        "resumo": "Hospedagem recomendada para lojas: o que procurar e parceiros.",
        "titulo": "Hospedagem para WooCommerce",
        "descricao": "O que procurar em uma hospedagem para loja WooCommerce: desempenho, cache, PHP, backup, suporte e parceiros recomendados.",
        "lead": "A hospedagem é o solo onde a loja cresce. Para WooCommerce, o básico não é espaço em disco: é PHP atualizado, banco de dados ágil, cache compatível com carrinho e suporte que entende de e-commerce.",
        "secoes": [
            ("O que verificar", "<p>Versões de PHP e MySQL suportadas, cache que não quebra carrinho e checkout, certificado SSL, backup diário, staging para testes e suporte com bom tempo de resposta. Pico de tráfego pede plano que escale sem susto.</p>"),
            ("Opções", "<p>Hospedagens compartilhadas boas servem para começar; hospedagens gerenciadas de WordPress/WooCommerce resolvem desempenho e manutenção para quem prefere focar na venda. O site oficial lista parceiros recomendados.</p>"),
        ],
        "resumo_itens": [
            "PHP atualizado, cache compatível com carrinho e SSL incluso.",
            "Backup diário e ambiente de staging para testes.",
            "Suporte que entende de WordPress e WooCommerce.",
        ],
        "cta": ("Ver hospedagens recomendadas", "https://woocommerce.com/hosting/"),
        "faq": [
            ("Hospedagem barata serve?", "Serve para começar, se atender aos requisitos mínimos. Medindo o crescimento, o gargalo costuma aparecer em datas de pico — aí vale migrar."),
            ("O que é staging?", "É uma cópia de teste da loja, no mesmo servidor: você atualiza e experimenta lá antes de publicar em produção."),
        ],
    },
    {
        "caminho": "/woocommerce/contrate-agencia/", "rotulo": "Contrate uma agência",
        "resumo": "Diretório de agências WooExpert para projetos e operação contínua.",
        "titulo": "Contrate uma agência WooCommerce",
        "descricao": "Como contratar agências especializadas em WooCommerce: diretório WooExpert, escopo de projeto, orçamento e critérios de escolha.",
        "lead": "Quando o projeto passa do que dá para fazer sozinho, agências especializadas entram: migração, integração com ERP e nota fiscal, desenho sob medida e operação contínua.",
        "secoes": [
            ("Onde procurar", "<p>O diretório de WooExperts lista agências certificadas, com portfólio e especialidades. Outra fonte são indicações de outras lojas — caso real vale mais que pitch.</p>"),
            ("Como contratar bem", "<p>Escreva o escopo antes de pedir orçamento, pergunte sobre manutenção pós-entrega, propriedade do código e prazos, e desconfie de orçamento muito abaixo do mercado. Loja é sistema contínuo, não projeto único.</p>"),
        ],
        "cta": ("Ver o diretório de agências", "https://woocommerce.com/experts/"),
        "faq": [
            ("Quanto custa um projeto?", "Varia muito com escopo, integrações e prazo. Peça orçamento com escopo escrito e itens discriminados."),
            ("E depois da entrega?", "Combine suporte e manutenção: loja precisa de atualizações, monitoramento e ajustes contínuos."),
        ],
    },
    {
        "caminho": "/woocommerce/pesquisa/", "rotulo": "Pesquisa de satisfação",
        "resumo": "Conte sua experiência e ajude a direcionar o produto.",
        "titulo": "Pesquisa de satisfação do cliente do WooCommerce",
        "descricao": "Participe da pesquisa de satisfação do WooCommerce: sua opinião orienta prioridades de produto e suporte.",
        "lead": "A pesquisa de satisfação é o canal curto entre quem usa e quem decide. As respostas alimentam prioridades de produto, suporte e documentação.",
        "secoes": [
            ("Por que responder", "<p>Respostas específicas valem mais que notas: o que travou, o que funcionou e o que faltou dizem mais do que uma estrela. É o tipo de feedback que muda roadmap.</p>"),
            ("Privacidade", "<p>Pesquisas oficiais explicam como os dados são usados e permitem anonimato quando a identificação não é necessária. Confira o aviso antes de responder.</p>"),
        ],
        "cta": ("Participar da pesquisa", "https://woocommerce.com/survey/"),
        "faq": [
            ("Leva muito tempo?", "Não: a pesquisa é curta e objetiva, pensada para não atrapalhar o trabalho."),
            ("Minhas respostas são anônimas?", "Depende da versão da pesquisa — o formulário informa se a identificação é opcional ou anônima."),
        ],
    },
    {
        "caminho": "/woocommerce/acessibilidade/", "rotulo": "Acessibilidade",
        "resumo": "Compromissos e práticas de acessibilidade do WooCommerce.",
        "titulo": "Acessibilidade no WooCommerce",
        "descricao": "Acessibilidade no WooCommerce e no ecossistema: padrões, compromissos, recursos e como reportar barreiras.",
        "lead": "Loja acessível vende mais e exclui menos. O WooCommerce trabalha com as Diretrizes de Acessibilidade para Conteúdo Web (WCAG) e mantém canal para reportar barreiras encontradas.",
        "secoes": [
            ("Na prática", "<p>Temas e blocos oficiais seguem padrões de navegação por teclado, contraste e estrutura semântica. Extensões de terceiros variam: teste teclado, leitor de tela e contraste antes de fechar a compra no seu tema.</p>"),
            ("Responsabilidade compartilhada", "<p>O núcleo dá a base; o tema, as extensões e o conteúdo da loja completam. Textos alternativos, formulários com rótulos e vídeos com legenda são trabalho do dia a dia da loja.</p>"),
        ],
        "cta": ("Ler sobre acessibilidade", "https://woocommerce.com/accessibility/"),
        "faq": [
            ("O WooCommerce atende a WCAG?", "O trabalho segue as diretrizes WCAG; o nível de conformidade varia conforme tema e extensões instalados — teste o seu contexto."),
            ("Como reportar uma barreira?", "Pelos canais oficiais indicados na página de acessibilidade, com descrição, navegador e assistiva usado."),
        ],
    },
    {
        "caminho": "/woocommerce/foruns/", "rotulo": "Fóruns de suporte",
        "resumo": "Fóruns da comunidade: dúvidas, respostas e casos reais.",
        "titulo": "Fóruns de suporte do WooCommerce",
        "descricao": "Os fóruns de suporte do WooCommerce e do WordPress: dúvidas respondidas pela comunidade, casos reais e busca de soluções.",
        "lead": "Os fóruns da comunidade são o maior arquivo de problemas resolvidos do ecossistema: quase todo erro de configuração já apareceu por lá, com resposta de quem passou pela mesma coisa.",
        "secoes": [
            ("Como usar bem", "<p>Busque antes de postar, inclua versões e mensagem de erro exata, e descreva o que já tentou. Tópico bem escrito recebe resposta mais rápido e ajuda quem chegar depois.</p>"),
            ("Onde postar", "<p>Dúvidas gerais do WooCommerce vão aos fóruns do WordPress; produtos pagos têm canal próprio de suporte com o desenvolvedor; problemas de servidor são com a hospedagem.</p>"),
        ],
        "cta": ("Abrir os fóruns", "https://wordpress.org/support/plugin/woocommerce/"),
        "faq": [
            ("A resposta é oficial?", "Não: fóruns são respondidos pela comunidade, com moderação. Para garantia de resposta, use o suporte do produto pago."),
            ("Consigo resposta em português?", "Os fóruns oficiais são em inglês; comunidades brasileiras têm grupos e fóruns próprios em português."),
        ],
    },
]

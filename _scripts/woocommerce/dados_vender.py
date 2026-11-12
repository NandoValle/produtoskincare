# Conteúdo das páginas do grupo "Vender" da seção WooCommerce.
# Cada página: caminho, rotulo (link), resumo (card), titulo, descricao, lead,
# secoes [(h2, html)], resumo_itens (opcional), cta/cta2 (opcional), faq [(q, a)].
PAGINAS = [
    {
        "caminho": "/woocommerce/precos/", "rotulo": "Preços do WooCommerce",
        "resumo": "O que é grátis e o que custa dinheiro: hospedagem, domínio, temas e extensões.",
        "titulo": "Preços do WooCommerce: o que é grátis e o que custa",
        "descricao": "O plugin WooCommerce é gratuito e de código aberto. Entenda onde entra o dinheiro: hospedagem, domínio, tema, extensões e taxas de pagamento.",
        "lead": "O WooCommerce em si é gratuito e de código aberto: baixar, instalar e usar não custa nada. O orçamento de uma loja vem de outras peças — hospedagem, domínio, tema, extensões e as taxas dos meios de pagamento.",
        "secoes": [
            ("O que é gratuito", "<p>O plugin WooCommerce, os temas gratuitos do diretório do WordPress, o aplicativo móvel e a documentação são grátis. Lojas pequenas podem começar sem pagar nada além da hospedagem e do domínio.</p>"),
            ("Onde costuma entrar o dinheiro", "<p><strong>Hospedagem</strong> com suporte a WordPress e WooCommerce; <strong>domínio</strong> anual; <strong>temas pagos</strong> quando o desenho pronto não basta; <strong>extensões</strong> para pagamentos, envios, notas fiscais e integrações — normalmente com licença anual; e as <strong>taxas dos gateways de pagamento</strong>, que variam por operadora.</p><p>Os valores mudam com frequência, então confira sempre a página oficial de preços e as páginas de cada extensão antes de comprar.</p>"),
        ],
        "resumo_itens": [
            "Plugin WooCommerce: gratuito e de código aberto.",
            "Custos comuns: hospedagem, domínio, tema, extensões e taxas de pagamento.",
            "Licenças de extensão costumam ser anuais, com renovação para continuar recebendo atualizações.",
        ],
        "cta": ("Ver preços oficiais", "https://woocommerce.com/pricing/"),
        "faq": [
            ("O WooCommerce é grátis mesmo?", "Sim. O plugin é gratuito e de código aberto. O que se paga são serviços ao redor: hospedagem, domínio, extensões, temas pagos e as taxas cobradas pelos meios de pagamento."),
            ("Quanto custa abrir uma loja do zero?", "Depende do tamanho. Uma loja simples pode sair pelo custo da hospedagem e do domínio; lojas com pagamentos locais, notas fiscais e integrações somam extensões com licença anual. Monte a lista de necessidades primeiro e só então compare preços."),
        ],
    },
    {
        "caminho": "/woocommerce/pagamentos/", "rotulo": "Pagamentos",
        "resumo": "Cartão, Pix, boleto e carteiras digitais na finalização da compra.",
        "titulo": "Pagamentos no WooCommerce: cartão, Pix, boleto e mais",
        "descricao": "Como aceitar pagamento na loja WooCommerce: gateways oficiais e extensões para Pix, boleto, cartão, Mercado Pago, Stripe e PayPal.",
        "lead": "Aceitar pagamento no WooCommerce é questão de instalar o gateway certo. No Brasil, as lojas costumam combinar Pix, boleto e cartão por meio de extensões de operadoras locais e internacionais.",
        "secoes": [
            ("Como funciona", "<p>O WooCommerce já traz transferência bancária, cheque, pagamento na entrega e cartão por gateways. Para Pix, boleto e adquirentes brasileiros, o caminho são extensões — como Mercado Pago, PagBank, Pagar.me, Stripe e PayPal, entre outras do Marketplace.</p>"),
            ("O que observar ao escolher", "<p>Compare a taxa por transação, o prazo de recebimento, a experiência no checkout (Pix com QR Code, cartão em uma página) e a qualidade da integração: extensões com manutenção ativa evitam problema em datas de pico.</p>"),
        ],
        "resumo_itens": [
            "Pix, boleto e cartão via extensões de gateway.",
            "Compare taxa, prazo de recebimento e manutenção da extensão.",
            "Teste o fluxo completo de compra antes de abrir a loja.",
        ],
        "cta": ("Ver gateways no Marketplace", "https://woocommerce.com/product-category/woocommerce-extensions/payment-gateways/"),
        "faq": [
            ("O WooCommerce cobra taxa sobre as vendas?", "Não. O WooCommerce não cobra comissão; as taxas vêm do gateway de pagamento escolhido (operadora de cartão, Pix ou carteira digital)."),
            ("Dá para usar Pix e boleto?", "Sim, por extensões de gateways que oferecem esses métodos. Confirme se a extensão é compatível com a sua versão do WooCommerce e do WordPress."),
        ],
    },
    {
        "caminho": "/woocommerce/personalizacao/", "rotulo": "Personalização sem programação",
        "resumo": "Editor de blocos, temas e customizador para mudar o visual sem código.",
        "titulo": "Personalização sem programação no WooCommerce",
        "descricao": "Edite páginas, cores, tipografia e o checkout com o editor de blocos do WordPress e o Customizer — sem escrever código.",
        "lead": "Dá para montar e ajustar a loja inteira sem programar: o editor de blocos do WordPress reorganiza páginas por arrastar e soltar, e o Customizador cuida de cores, fontes e cabeçalho.",
        "secoes": [
            ("Ferramentas visuais", "<p>O editor de blocos monta a página inicial, páginas de produto, carrinho e checkout com blocos do WooCommerce. Temas modernos expõem cores, tipografia e espaçamento nos estilos globais, e o Customizador mostra a prévia em tempo real.</p>"),
            ("Quando é hora de chamar código", "<p>Cálculos de frete muito específicos, integrações internas e comportamentos fora do padrão ainda pedem um desenvolvedor. Para o resto — layout, textos, imagens e fluxos de compra — as ferramentas visuais resolvem.</p>"),
        ],
        "cta": ("Ver temas", "/woocommerce/temas/"),
        "faq": [
            ("Preciso saber programar para abrir uma loja?", "Não. Com um tema compatível com blocos, a maior parte da montagem acontece no editor visual. Código é necessário apenas para personalizações muito específicas."),
            ("O que é o editor de blocos?", "É o editor do WordPress baseado em blocos: cada trecho da página (texto, imagem, grade de produtos, botão) é um bloco que se move e se configura visualmente."),
        ],
    },
    {
        "caminho": "/woocommerce/marketing/", "rotulo": "Marketing",
        "resumo": "Cupons, e-mail, SEO e integrações para atrair e trazer de volta clientes.",
        "titulo": "Marketing no WooCommerce",
        "descricao": "Cupons de desconto, listas de e-mail, SEO, Google e redes sociais: as ferramentas de marketing do WooCommerce e suas extensões.",
        "lead": "Crescer uma loja é combinar cupons e campanhas com uma base de e-mail bem cuidada e um SEO sólido. O WooCommerce traz o básico e o Marketplace cobre o resto.",
        "secoes": [
            ("O que já vem pronto", "<p>Cupons de desconto com regras, gestão de pedidos e relatórios, URLs amigáveis e sitemaps via plugins de SEO. A integração com Google (Analytics, Merchant Center) e com redes sociais acontece por extensões oficiais ou parceiras.</p>"),
            ("Boas práticas", "<p>Comece pela base: páginas de produto com fotos boas, descrição clara e avaliações. Depois ative recuperação de carrinho abandonado, e-mails pós-compra e campanhas segmentadas — em geral com extensões de automação de marketing.</p>"),
        ],
        "cta": ("Ver extensões de marketing", "https://woocommerce.com/product-category/woocommerce-extensions/marketing/"),
        "faq": [
            ("O WooCommerce tem cupom de desconto?", "Sim, é um recurso nativo: dá para criar cupons com percentual, valor fixo, regras de produto, limite de uso e validade."),
            ("Como conectar com Google e redes sociais?", "Por extensões de integração que sincronizam o catálogo e instalam pixels de conversão. Escolha extensões com atualização frequente e boa avaliação."),
        ],
    },
    {
        "caminho": "/woocommerce/checkout/", "rotulo": "Checkout",
        "resumo": "Carrinho e finalização em blocos, com campos flexíveis e menos abandono.",
        "titulo": "Checkout no WooCommerce",
        "descricao": "Checkout em blocos, campos personalizados, compra em uma página e recursos para reduzir o abandono de carrinho.",
        "lead": "O checkout é onde a venda acontece — ou não. O WooCommerce moderno traz carrinho e finalização em blocos, com layout flexível e campos que se ajustam ao negócio.",
        "secoes": [
            ("Recursos", "<p>Blocos de carrinho e checkout com reordenação visual, campos de entrega e cobrança, opções de retirada local, cupom aplicado no carrinho e resumo fixo do pedido. Extensões adicionam compra em uma página, checkout multi-etapas e campos condicionais.</p>"),
            ("Reduzindo o abandono", "<p>Menos campos, opções de pagamento visíveis, cálculo de frete antes da finalização e confiança (política de troca, contato) derrubam o abandono. Meça antes e depois de cada mudança.</p>"),
        ],
        "resumo_itens": [
            "Carrinho e checkout em blocos, editáveis visualmente.",
            "Campos flexíveis e retirada local nativos.",
            "Extensões para checkout em uma página e campos condicionais.",
        ],
        "faq": [
            ("Dá para personalizar os campos do checkout?", "Sim. Os blocos permitem ajustar campos de entrega e cobrança; para regras mais complexas, há extensões de campos personalizados e condicionais."),
            ("O que é checkout em blocos?", "É a versão do checkout baseada no editor de blocos: você monta o layout visualmente, com blocos de campos, resumo do pedido e pagamento."),
        ],
    },
    {
        "caminho": "/woocommerce/envios/", "rotulo": "Envios",
        "resumo": "Zonas de envio, frete fixo, grátis, retirada e transportadoras por extensão.",
        "titulo": "Envios no WooCommerce: frete, zonas e transportadoras",
        "descricao": "Configure zonas de envio, frete fixo, frete grátis, retirada local e integrações com transportadoras e Correios.",
        "lead": "O WooCommerce calcula frete por zonas geográficas: cada zona combina os métodos que fazem sentido — frete fixo, grátis, retirada local ou cotação de transportadora via extensão.",
        "secoes": [
            ("Configuração básica", "<p>Defina zonas (por país, estado ou CEP), escolha os métodos de cada zona e estabeleca regras de frete grátis por valor mínimo ou cupom. Retirada local é nativa e útil para lojas com loja física.</p>"),
            ("Cotação em tempo real", "<p>Extensões de transportadoras e dos Correios consultam peso, dimensões e CEP para devolver valores ao cliente. Confira se a extensão cobre suas dimensões e embalagens antes de depender dela.</p>"),
        ],
        "cta": ("Ver extensões de envio", "https://woocommerce.com/product-category/woocommerce-extensions/shipping/"),
        "faq": [
            ("O WooCommerce calcula frete por CEP?", "O núcleo calcula por zonas. A cotação automática por CEP com valor de transportadora ou Correios vem de extensões."),
            ("Dá para oferecer frete grátis?", "Sim, nativamente: por zona, com valor mínimo de pedido ou cupom de frete grátis."),
        ],
    },
    {
        "caminho": "/woocommerce/app-movel/", "rotulo": "Aplicativo móvel",
        "resumo": "Gerencie pedidos e produtos pelo celular, grátis, para iOS e Android.",
        "titulo": "Aplicativo móvel do WooCommerce",
        "descricao": "O aplicativo gratuito do WooCommerce para iOS e Android: pedidos, notificações, produtos e métricas da loja na palma da mão.",
        "lead": "O aplicativo móvel do WooCommerce é gratuito e está nas lojas da Apple e do Google. Com ele, a loja cabe no bolso: pedidos, notificações de venda e métricas em tempo real.",
        "secoes": [
            ("O que dá para fazer", "<p>Receber aviso a cada venda, mudar status de pedido, responder clientes, cadastrar produtos com fotos da câmera e acompanhar faturamento e visitas. A interface foi desenhada para o dia a dia do lojista, não para a mesa de trabalho.</p>"),
            ("Para quem é", "<p>Quem vende fora do horário comercial, atende feiras e eventos ou só quer acompanhar a loja sem abrir o computador. Conecta à mesma loja do site — não é um canal de venda separado.</p>"),
        ],
        "cta": ("Baixar para iPhone", "https://apps.apple.com/app/woo-commerce/id1485887955"),
        "cta2": ("Baixar para Android", "https://play.google.com/store/apps/details?id=com.woocommerce.android"),
        "faq": [
            ("O aplicativo é pago?", "Não. É gratuito para iOS e Android e se conecta à sua loja WooCommerce existente."),
            ("Precisa de internet para usar?", "Sim: o app consulta a loja em tempo real. As ações valem assim que sincronizam com o site."),
        ],
    },
    {
        "caminho": "/woocommerce/empresarial/", "rotulo": "Comércio eletrônico empresarial",
        "resumo": "WooCommerce em alto volume: infraestrutura, suporte e parceiros para grandes lojas.",
        "titulo": "Comércio eletrônico empresarial com WooCommerce",
        "descricao": "WooCommerce para empresas e lojas de alto volume: infraestrutura gerenciada, suporte dedicado e parceiros especializados.",
        "lead": "Empresas que vendem muito precisam de mais que um plugin: infraestrutura que aguenta pico de tráfego, suporte com SLA e parceiros que conhecem a fundo o ecossistema.",
        "secoes": [
            ("O que muda em escala", "<p>Catálogos grandes, alto volume de pedidos, integrações com ERP e nota fiscal, multi-moeda e multi-país exigem hospedagem gerenciada, cache bem configurado e testes de carga. O WooCommerce continua no centro — o que muda é o entorno.</p>"),
            ("Caminhos", "<p>Hospedagem especializada em WordPress/WooCommerce, agências WooExpert para implementação e suporte premium do próprio WooCommerce para produtos oficiais. Para times internos, a documentação e as APIs cobrem integrações sob medida.</p>"),
        ],
        "cta": ("Falar com vendas", "https://woocommerce.com/contact/"),
        "faq": [
            ("O WooCommerce aguenta lojas grandes?", "Sim — muitas lojas de alto volume rodam WooCommerce. O dimensionamento depende de hospedagem, cache, extensões bem feitas e monitoramento."),
            ("Existe suporte empresarial?", "Sim. Há suporte pago para produtos oficiais, hospedagem gerenciada com suporte e agências certificadas para operação contínua."),
        ],
    },
    {
        "caminho": "/woocommerce/marketplace/", "rotulo": "Marketplace",
        "resumo": "Loja oficial de extensões e temas, com curadoria e suporte dos desenvolvedores.",
        "titulo": "Marketplace do WooCommerce",
        "descricao": "O Marketplace oficial: extensões e temas com curadoria, garantia, suporte dos desenvolvedores e atualizações.",
        "lead": "O Marketplace do WooCommerce é a loja oficial de extensões e temas. Tudo passa por curadoria, com suporte dos desenvolvedores, atualizações e garantia de reembolso.",
        "secoes": [
            ("O que se encontra lá", "<p>Extensões de pagamento, envio, marketing, assinaturas, reservas, membros, contabilidade e integrações com o mercado brasileiro; temas com suporte e documentação. Dá para filtrar por categoria, preço e avaliação.</p>"),
            ("Por que comprar no Marketplace", "<p>Compatibilidade testada, política de reembolso, canal de suporte direto com o desenvolvedor e atualizações pelo painel do WordPress. Fora dele, o cuidado com a origem do código é seu.</p>"),
        ],
        "cta": ("Explorar o Marketplace", "https://woocommerce.com/marketplace/"),
        "faq": [
            ("As extensões têm garantia?", "Sim: compras no Marketplace oficial têm política de reembolso e suporte do desenvolvedor — confira os termos de cada produto."),
            ("Preciso renovar a licença?", "Licenças de extensão costumam ser anuais. Sem renovação, o produto continua funcionando, mas sem atualizações e suporte."),
        ],
    },
    {
        "caminho": "/woocommerce/extensoes/", "rotulo": "Extensões do WooCommerce",
        "resumo": "Pagamentos, assinaturas, reservas, contabilidade: a loja cresce por extensões.",
        "titulo": "Extensões do WooCommerce",
        "descricao": "O que são as extensões do WooCommerce e como escolher: pagamentos, envios, assinaturas, reservas, contabilidade e integrações.",
        "lead": "Extensões são plug-ins que ampliam a loja: um novo meio de pagamento, cálculo de frete, venda por assinatura, reserva de horário, nota fiscal. O núcleo enxuto; a loja cresce por extensões.",
        "secoes": [
            ("Como escolher", "<p>Priorize extensões do Marketplace oficial ou de desenvolvedores conhecidos. Confira data da última atualização, compatibilidade com a sua versão, qualidade do suporte e se resolve o problema de verdade — muita funcionalidade se resolve com configuração, não com extensão.</p>"),
            ("Categorias comuns", "<p>Pagamentos e gateways; envios e cotação; assinaturas e pagamentos recorrentes; reservas e agendamentos; membros e área do cliente; contabilidade e fiscal; marketing e automação; busca, filtro e merchandising.</p>"),
        ],
        "cta": ("Ver todas as extensões", "https://woocommerce.com/products/"),
        "faq": [
            ("Muitas extensões deixam a loja lenta?", "Podem. Cada extensão soma código; prefira poucas e bem feitas, e meça o desempenho depois de instalar qualquer uma."),
            ("Extensão grátis é confiável?", "Depende da origem. O repositório oficial do WordPress tem critérios; ainda assim, verifique atualizações, avaliações e suporte antes de instalar em loja em produção."),
        ],
    },
    {
        "caminho": "/woocommerce/temas/", "rotulo": "Temas do WooCommerce",
        "resumo": "Temas gratuitos e pagos, compatíveis com blocos, no diretório oficial.",
        "titulo": "Temas do WooCommerce",
        "descricao": "Temas gratuitos e pagos para lojas WooCommerce: diretório oficial, compatibilidade com blocos e suporte dos desenvolvedores.",
        "lead": "O tema define o desenho da loja. Os temas compatíveis com blocos funcionam com o editor visual do WordPress e com os blocos do WooCommerce — e mudam de visual sem tocar em código.",
        "secoes": [
            ("Gratuitos e pagos", "<p>O diretório do WordPress tem temas gratuitos testados, alguns feitos pelo próprio Woo. Os temas pagos do Marketplace vêm com suporte, documentação e atualizações. O preço único costuma incluir licença por ano de suporte.</p>"),
            ("O que verificar", "<p>Compatibilidade com blocos e com a última versão do WooCommerce, velocidade, suporte a acessibilidade, avaliações reais e o desenho nas telas de produto, carrinho e checkout — é onde o cliente decide.</p>"),
        ],
        "cta": ("Ver temas no Marketplace", "https://woocommerce.com/products/"),
        "faq": [
            ("Qual tema é bom para começar?", "Um tema gratuito compatível com blocos resolve o começo. Troque por um pago quando o desenho ou o suporte justificarem."),
            ("Dá para mudar de tema depois?", "Sim: produtos, pedidos e conteúdo ficam no banco de dados, independentes do tema. O visual é que muda."),
        ],
    },
    {
        "caminho": "/woocommerce/novidade/", "rotulo": "Novidade",
        "resumo": "O que há de novo: lançamentos, melhorias e recursos recentes do WooCommerce.",
        "titulo": "Novidade: o que há de novo no WooCommerce",
        "descricao": "Lançamentos, melhorias e recursos recentes do WooCommerce: blocos, performance, aplicativo móvel e Marketplace.",
        "lead": "O WooCommerce evolui em ciclos curtos: novos blocos, ganhos de performance, melhorias no aplicativo móvel e produtos novos feitos pelo Woo. Esta página resume o tipo de novidade que sai por aqui.",
        "secoes": [
            ("Onde acompanhar", "<p>A página de atualizações de produto e o blog oficial trazem o detalhamento de cada versão. Versões saem com frequência — mantenha loja, tema e extensões atualizados para receber melhorias e correções de segurança.</p>"),
            ("Como experimentar com segurança", "<p>Teste novidades em ambiente de homologação antes de aplicar em produção, e confira a compatibilidade das extensões instaladas. Atualizar sem teste é o jeito mais comum de quebrar uma loja.</p>"),
        ],
        "cta": ("Ver atualizações", "/woocommerce/atualizacoes/"),
        "faq": [
            ("Com que frequência sai versão nova?", "O WooCommerce lança versões regularmente ao longo do ano, com correções contínuas entre as versões maiores."),
            ("Devo atualizar sempre?", "Sim, mas com teste: atualizações trazem correções de segurança e melhorias. Rode em homologação antes de subir em produção."),
        ],
    },
    {
        "caminho": "/woocommerce/recursos-basicos/", "rotulo": "Recursos básicos",
        "resumo": "Produtos, pedidos, estoque, impostos, relatórios e SEO — a base da loja.",
        "titulo": "Recursos básicos do WooCommerce",
        "descricao": "Os recursos que vêm no núcleo do WooCommerce: catálogo de produtos, carrinho, pedidos, estoque, cupons, impostos e relatórios.",
        "lead": "Antes das extensões, o núcleo. O WooCommerce já entrega o essencial de uma loja: catálogo, carrinho, checkout, gestão de pedidos, estoque, impostos e relatórios.",
        "secoes": [
            ("Catálogo e vendas", "<p>Produtos simples e variáveis (tamanho, cor), produtos virtuais e digitais, agrupados e externos; avaliações, categorias, etiquetas e atributos. Carrinho e checkout nativos, com cupons e cálculo de impostos.</p>"),
            ("Operação", "<p>Gestão de pedidos com status e notas, controle de estoque com avisos de falta, e-mails transacionais automáticos para cliente e lojista, relatórios de vendas, clientes e estoque, e estrutura amigável para SEO.</p>"),
        ],
        "resumo_itens": [
            "Produtos simples, variáveis, digitais e externos.",
            "Pedidos, estoque, cupons, impostos e e-mails automáticos.",
            "Relatórios de venda e base pronta para SEO.",
        ],
        "cta": ("Ver a página do produto", "https://woocommerce.com/"),
        "faq": [
            ("Vende produto digital com WooCommerce?", "Sim: downloads digitais são nativos, com controle de acesso e entrega automática após o pagamento."),
            ("O WooCommerce controla estoque?", "Sim: quantidade por produto e variação, aviso de estoque baixo e bloqueio de compra quando acaba."),
        ],
    },
    {
        "caminho": "/woocommerce/colecoes/", "rotulo": "Coleções",
        "resumo": "Conjuntos curados de extensões e temas por tipo de negócio.",
        "titulo": "Coleções do WooCommerce",
        "descricao": "Coleções curadas de extensões e temas por tipo de negócio: moda, alimentos, assinaturas, serviços e mais.",
        "lead": "Em vez de procurar extensão por extensão, as coleções reúnem conjuntos prontos por tipo de negócio — o atalho para montar a loja com o que já é combinado entre si.",
        "secoes": [
            ("Como funcionam", "<p>Cada coleção reúne temas e extensões que costumam andar juntos: moda e vestuário, alimentos e bebidas, assinaturas, serviços e agendamentos, educação, mercado digital. Serve de ponto de partida, não de receita fechada.</p>"),
            ("Usando bem", "<p>Escolha a coleção mais próxima do seu negócio, liste o que de fato precisa hoje e deixe o resto para depois. Loja enxuta é mais rápida de montar e mais fácil de manter.</p>"),
        ],
        "cta": ("Ver coleções", "https://woocommerce.com/collections/"),
        "faq": [
            ("As coleções são pacotes fechados?", "Não: são curadorias de referência. Você escolhe os itens um a um conforme a necessidade."),
            ("Todas as coleções incluem tema?", "Algumas trazem temas junto; outras focam em extensões. A página de cada coleção lista o conteúdo."),
        ],
    },
    {
        "caminho": "/woocommerce/desenvolvido-pelo-woo/", "rotulo": "Desenvolvido pelo Woo",
        "resumo": "Produtos oficiais: pagamentos, envio, impostos e ferramentas feitas pelo próprio Woo.",
        "titulo": "Desenvolvido pelo Woo",
        "descricao": "Os produtos oficiais feitos pela equipe do Woo: pagamentos, envio, impostos, extensões e ferramentas com suporte direto.",
        "lead": "Nem toda extensão é de terceiros. A equipe do Woo mantém um conjunto de produtos oficiais — de pagamentos a envio e impostos — com suporte direto de quem escreveu o código.",
        "secoes": [
            ("O que é oficial", "<p>Produtos assinados pelo Woo aparecem no Marketplace com a marca de desenvolvedor oficial. Incluem soluções de pagamento, cálculo de envio, impostos, assinaturas e ferramentas de gestão, além do próprio núcleo e dos blocos.</p>"),
            ("Por que importa", "<p>Compatibilidade testada com cada versão do WooCommerce, suporte oficial e um canal único quando algo dá errado. Para lojas que dependem da venda, essa previsibilidade vale o preço.</p>"),
        ],
        "cta": ("Ver produtos oficiais", "https://woocommerce.com/products/"),
        "faq": [
            ("Produtos do Woo são pagos?", "Alguns são gratuitos, outros pagos com licença anual. A página de cada produto traz o preço e o que está incluído."),
            ("O suporte é diferente?", "Sim: produtos desenvolvidos pelo Woo têm suporte prestado pela própria equipe, no canal oficial."),
        ],
    },
]

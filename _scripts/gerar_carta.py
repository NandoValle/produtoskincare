# -*- coding: utf-8 -*-
"""Gera /independencia/: a carta aberta sobre os links de afiliado, com o formulário de retorno.

O texto fica aqui. O formulário usa o canais.js (data-ps-enviar): a resposta sai do e-mail ou do
WhatsApp de quem escreve, e o site não guarda nada.

Regras do texto, para quem for editar:
  - Não anuncia preço, plano nem data: isso só depois de ouvir as respostas.
  - Não usa "premium", "exclusivo" nem "upgrade".
  - O que a carta diz sobre os links de afiliado tem de bater com /sobre/#afiliado.

Uso, na raiz do site:

    python3 -I _scripts/gerar_carta.py
    python3 -I _scripts/seo.py
    python3 -I _scripts/prontidao.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagina_base import RAIZ, pagina  # noqa: E402

PUBLICADA_EM = ("2026-11-24", "24 de novembro de 2026")

CSS = """
.ca-form{display:flex;flex-direction:column;gap:18px}
.ca-form[hidden]{display:none}
.ca-form fieldset{border:0;margin:0;padding:0;display:flex;flex-direction:column;gap:2px;min-width:0}
.ca-form legend,.ca-form>div>label{font-weight:600;padding:0;margin-bottom:6px;display:block}
.ca-form fieldset label{display:flex;gap:10px;align-items:center;min-height:44px;cursor:pointer}
.ca-form input[type=radio]{width:20px;height:20px;flex:0 0 20px;accent-color:var(--rosa)}
.ca-form textarea{width:100%;font:inherit;padding:12px 14px;border:1.5px solid var(--linha-2,var(--linha));border-radius:12px;background:var(--fundo);color:var(--tinta);resize:vertical}
.ca-form textarea:focus{outline:3px solid var(--rosa);outline-offset:2px}
.ca-botoes{display:flex;flex-wrap:wrap;gap:8px}
.ca-btn{font:inherit;font-weight:600;min-height:48px;padding:0 22px;border-radius:999px;border:0;background:var(--rosa);color:var(--sobre-rosa,#fff);cursor:pointer}
.ca-btn.ca-sec{background:transparent;color:var(--tinta);border:1.5px solid var(--linha-2,var(--linha))}
.ca-btn[hidden]{display:none}
@media(prefers-color-scheme:dark){.ca-btn:not(.ca-sec){color:#28131b}}
html[data-tema=claro] .ca-btn:not(.ca-sec){color:#fff}html[data-tema=escuro] .ca-btn:not(.ca-sec){color:#28131b}
"""

CORPO = f"""<article>
<div class="ig-cab">
<p class="ig-rotulo">Carta aberta</p>
<h1>O problema dos links de afiliado, inclusive os nossos</h1>
<p class="ig-lede">Este site ganha dinheiro quando você compra. Esta carta explica o que isso significa, por que nos incomoda e o que queremos testar no lugar. No fim, pedimos a sua opinião.</p>
<p class="ig-meta">Por Equipe Produto Skincare, <a href="/sobre/#quem-escreve">texto escrito com IA</a> · Publicada em <time datetime="{PUBLICADA_EM[0]}">{PUBLICADA_EM[1]}</time></p>
</div>

<section aria-labelledby="ca-hoje">
<h2 id="ca-hoje">Como o site se paga hoje</h2>
<p>Muitos botões de loja daqui são links de afiliado: Amazon, Shopee, Mercado Livre, TikTok Shop. Se você compra por um deles, a loja paga uma comissão ao site, e o preço para você é o mesmo. Isso está avisado no rodapé de todas as páginas e explicado na página <a href="/sobre/#afiliado">Sobre</a>.</p>
<p>Além da comissão, o site vende um material próprio, o <a href="/programa-12-semanas/">Programa 12 Semanas</a>, em pagamento único. O resto é gratuito e sem cadastro.</p>
</section>

<section aria-labelledby="ca-problema">
<h2 id="ca-problema">Onde está o problema</h2>
<p>A comissão só existe quando alguém compra. Um site pago assim ganha mais quando você compra mais vezes, quando escolhe o produto mais caro e quando compra na loja que paga comissão. E não ganha nada quando a resposta honesta é “não compre”: use o que já tem, o mais barato resolve, esse passo é dispensável.</p>
<p>Não é preciso má-fé para esse incentivo agir. Basta ele existir, todos os dias, sempre na mesma direção.</p>
<p>Essa tensão está dentro do próprio site. O <a href="/ferramentas/despensa/">modo despensa</a> serve para montar a rotina com o que você já tem em casa. O <a href="/ferramentas/rever-rotina/">Rever minha rotina</a> serve para tirar passos. O <a href="/ferramentas/equivalente/">Equivalente mais barato</a> serve para pagar menos. Cada vez que uma dessas ferramentas funciona, o site deixa de ganhar.</p>
</section>

<section aria-labelledby="ca-regras">
<h2 id="ca-regras">O que já fazemos, e por que não basta</h2>
<p>As regras de hoje são estas:</p>
<ul>
<li>Nenhuma marca paga para entrar no catálogo nem para subir de posição.</li>
<li>Não há texto patrocinado nem produto analisado em troca de envio gratuito.</li>
<li>Quando o produto que faz mais sentido não tem programa de afiliado, ele entra do mesmo jeito, sem link.</li>
<li>O botão de compra só aparece com link direto para o anúncio conferido. Link de busca aparece como “sem oferta verificada”.</li>
<li>O selo de evidência vem do ativo e dos estudos, não da loja.</li>
</ul>
<p>Todas elas são promessas: para valerem, você precisa confiar na nossa palavra. O incentivo continua lá. A única forma de tirá-lo é o site não depender de comissão.</p>
</section>

<section aria-labelledby="ca-teste">
<h2 id="ca-teste">O que queremos testar</h2>
<p>Um modelo em que quem paga o site é você, e não a loja: uma assinatura para quem quiser sustentar um site de skincare que não precise de comissão para existir.</p>
<p>Ainda não há plano, preço nem data. Antes de desenhar qualquer coisa, queremos ouvir quem usa o site. Pode ser que a resposta seja “não vale a pena”, e é melhor saber disso agora.</p>
</section>

<section class="ig-caixa" aria-labelledby="ca-fica">
<h2 id="ca-fica">O que não muda</h2>
<ul>
<li>O <a href="/provador/">provador</a> (quiz e selfie), as rotinas, os guias, o blog e as ferramentas continuam gratuitos e sem cadastro. A estimativa do seu tipo de pele não vai para trás de pagamento.</li>
<li>Os links de afiliado continuam por enquanto, avisados como hoje. Tirá-los de uma vez deixaria o site sem receita: são eles que pagam a parte gratuita enquanto o teste acontece.</li>
<li>Nenhuma marca paga para aparecer. Isso não está em teste.</li>
</ul>
</section>

<section aria-labelledby="ca-dados">
<h2 id="ca-dados">Um primeiro passo, já no ar</h2>
<p>O catálogo do site agora está em <a href="/dados-abertos/">dados abertos</a>: produtos, preços com a data em que foram conferidos e o histórico de fórmulas, para baixar e reutilizar. Os links de loja desses arquivos saem sem identificador de afiliado. É pouco dado ainda, e a página diz exatamente quanto.</p>
</section>

<section class="ig-caixa" aria-labelledby="ca-opine">
<h2 id="ca-opine">Diga o que você pensa</h2>
<p>São três perguntas. Só a primeira é obrigatória.</p>
<form class="ca-form" data-ps-enviar="Resposta à carta sobre afiliados" data-evento="carta/resposta" hidden>
<fieldset>
<legend>Você pagaria uma assinatura para manter um site de skincare sem comissão de loja?</legend>
<label><input type="radio" name="pagaria" data-rotulo="Pagaria uma assinatura" value="Sim" required> Sim</label>
<label><input type="radio" name="pagaria" data-rotulo="Pagaria uma assinatura" value="Talvez, depende do preço e do que vier junto"> Talvez, depende do preço e do que vier junto</label>
<label><input type="radio" name="pagaria" data-rotulo="Pagaria uma assinatura" value="Não"> Não</label>
</fieldset>
<div>
<label for="ca-sim">O que faria você assinar?</label>
<textarea id="ca-sim" name="assinaria" data-rotulo="O que me faria assinar" rows="4" placeholder="Ex.: saber quando a fórmula de um produto que eu uso mudou"></textarea>
</div>
<div>
<label for="ca-nao">O que faria você não assinar?</label>
<textarea id="ca-nao" name="nao_assinaria" data-rotulo="O que me faria não assinar" rows="4" placeholder="Ex.: se o provador passasse a ser pago"></textarea>
</div>
<div class="ca-botoes">
<button type="button" class="ca-btn" data-via="email">Enviar por e-mail</button>
<button type="button" class="ca-btn ca-sec" data-via="whatsapp">Enviar pelo WhatsApp</button>
</div>
<p class="ig-nota" data-ps-enviado hidden>Abrimos o seu aplicativo com a resposta pronta. Ela só chega até nós depois que você enviar por lá.</p>
<p class="ig-nota">A resposta sai do seu próprio aplicativo: o site não guarda o que você escreve. Usamos o que você enviar só para decidir os próximos passos, e não publicamos seu nome nem seu contato.</p>
</form>
<noscript><p>Sem JavaScript, escreva para contato@produtoskincare.com.br com o assunto “Resposta à carta sobre afiliados”.</p></noscript>
<p>Críticas valem tanto quanto apoio. Se alguma recomendação do site parecer estar ali só pela comissão, <a href="/contato/">diga qual</a>.</p>
</section>

<section aria-labelledby="ca-leia">
<h2 id="ca-leia">Leia também</h2>
<ul class="ig-rel">
<li><a href="/sobre/#afiliado">Links de afiliado, e o que a comissão não compra</a></li>
<li><a href="/dados-abertos/">Dados abertos</a></li>
<li><a href="/ferramentas/extrato-cosmetico/">Extrato do cosmético</a></li>
</ul>
</section>
</article>"""


def main():
    html = pagina(
        titulo="O problema dos links de afiliado, inclusive os nossos",
        descricao=("Carta aberta do Produto Skincare: como o site ganha com links de afiliado, por que esse incentivo "
                   "incomoda e o modelo pago pelo leitor que queremos testar. Diga o que você pensa."),
        caminho="/independencia/", trilha=[("/", "Início"), ("/sobre/", "Sobre"), (None, "Carta aberta")],
        corpo=CORPO, css_extra=CSS,
        aviso="Conteúdo informativo, não substitui consulta com dermatologista.")
    destino = RAIZ / "independencia" / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    print("gerada /independencia/")


if __name__ == "__main__":
    main()

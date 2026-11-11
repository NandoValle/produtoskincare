"""Regression tests for factual extraction; does not regenerate site files."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_site import montar_schema, json_script

SITE = "https://produtoskincare.com.br"


class SchemaFactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for location in ["index.html", "blog/index.html", "produtos/index.html"]:
            path = self.root / location
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def graph(self, body, lang="pt-BR", path="/blog/teste/", article=True, head=""):
        source = f'<html lang="{lang}"><head><link rel="canonical" href="{SITE}{path}">{head}</head><body><a href="/">Produto Skincare</a><main>{body}</main></body></html>'
        info = SimpleNamespace(title="Título da página", meta={"description": "Descrição da página"})
        return montar_schema(self.root, SITE, "Produto Skincare", path, info, source, article)["@graph"]

    def one(self, graph, kind):
        return next(n for n in graph if n["@type"] == kind)

    def test_english_dates_and_untruncated_heading(self):
        heading = "Retinol and your skin " * 8
        graph = self.graph(f'<h1>{heading}</h1><p class="ig-meta">By the Produto Skincare team · Updated on <time datetime="2026-11-04">November 4, 2026</time></p><p class="sub">Published on November 2, 2026 · 6-minute read</p>', lang="en")
        article = self.one(graph, "Article")
        self.assertEqual(article["inLanguage"], "en")
        self.assertEqual(article["headline"], heading.strip())
        self.assertEqual(article["datePublished"], "2026-11-02")
        self.assertEqual(article["dateModified"], "2026-11-04")
        self.assertEqual(article["author"], {"@id": SITE + "/#equipe"})

    def test_spanish_date(self):
        article = self.one(self.graph('<h1>Retinol</h1><p class="ig-meta">Por el equipo de Produto Skincare · Actualizado el 4 de noviembre de 2026</p><p class="sub">Publicado el 2 de noviembre de 2026</p>', lang="es"), "Article")
        self.assertEqual((article["inLanguage"], article["datePublished"], article["dateModified"]), ("es", "2026-11-02", "2026-11-04"))

    def test_no_inferred_update_or_author_or_generic_image(self):
        article = self.one(self.graph('<h1>Notícia</h1><p class="sub">Publicado em 9 de novembro de 2026</p><ul><li>Fonte. Atualizado em 5 de novembro de 2026.</li></ul>', head='<meta property="og:image" content="/img/og/noticia.jpg">'), "Article")
        self.assertEqual(article["datePublished"], "2026-11-09")
        self.assertFalse({"dateModified", "author", "image"} & article.keys())

    def test_hidden_byline_and_script_dates_ignored(self):
        article = self.one(self.graph('<h1>Artigo</h1><p class="ig-meta" hidden>Por Equipe Produto Skincare · Atualizado em 4 de novembro de 2026</p><script>"Publicado em 1 de novembro de 2026"</script>'), "Article")
        self.assertFalse({"datePublished", "dateModified", "author"} & article.keys())

    def test_actual_cover_and_exact_trail(self):
        graph = self.graph('<nav class="ig-trilha"><ol><li><a href="/">Início</a></li><li><a href="/blog/">Leituras</a></li><li aria-current="page">Guia</li></ol></nav><h1>Guia completo</h1><figure class="capa-artigo"><img src="/img/blog/real.webp"></figure>')
        self.assertEqual(self.one(graph, "Article")["image"], SITE + "/img/blog/real.webp")
        self.assertEqual([n["name"] for n in self.one(graph, "BreadcrumbList")["itemListElement"]], ["Início", "Leituras", "Guia"])

    def test_product_from_visible_offer(self):
        body = '<h1>Gel real</h1><p class="ig-meta">Marca Real · gel · Atualizado em 4 de novembro de 2026</p><p class="ig-lede">Limpeza suave. 4.8★ na loja.</p><div class="pd-compra"><p class="pd-preco">R$ 1.234,56</p><a rel="sponsored noopener" href="https://loja.example/produto">Ver na loja</a></div>'
        item = self.one(self.graph(body, path="/produtos/gel/", article=False), "Product")
        self.assertEqual(item["offers"], {"@type": "Offer", "price": "1234.56", "priceCurrency": "BRL", "url": "https://loja.example/produto"})
        self.assertEqual(item["description"], "Limpeza suave.")
        self.assertEqual(item["brand"]["name"], "Marca Real")
        self.assertFalse({"image", "aggregateRating", "gtin"} & item.keys())

    def test_missing_product_offer_is_not_invented(self):
        item = self.one(self.graph('<h1>Gel real</h1>', path="/produtos/gel/", article=False), "Product")
        self.assertNotIn("offers", item)
        self.assertNotIn("brand", item)

    def test_affiliate_price_keeps_visible_conditions_without_inferred_commerce(self):
        terms = "Na loja, em 02/11/2026. Preço muda: vale o mostrado na loja na hora da compra."
        affiliate = "Link de afiliado: posso receber comissão, sem custo extra."
        body = f'<h1>Gel real</h1><div class="pd-compra"><p class="pd-preco">R$ 96,90</p><p class="ig-nota">{terms}</p><a rel="sponsored" href="https://loja.example/produto">Ver na loja</a><p class="ig-nota">{affiliate}</p><p class="ig-nota" hidden>Frete grátis e estoque garantido.</p></div>'
        item = self.one(self.graph(body, path="/produtos/gel/", article=False), "Product")
        self.assertEqual(item["offers"], {
            "@type": "Offer", "price": "96.90", "priceCurrency": "BRL",
            "description": terms + " " + affiliate, "url": "https://loja.example/produto"})
        self.assertFalse({"review", "aggregateRating", "image"} & item.keys())

    def test_search_and_internal_links_are_not_claimed_as_purchase_urls(self):
        for href in ["https://www.amazon.com.br/s?k=gel", "https://shopee.com.br/search?keyword=gel",
                     "https://lista.mercadolivre.com.br/gel", "/produtos/gel/",
                     SITE.replace("://", "://www.") + "/", SITE.replace("://", "://checkout.") + "/"]:
            with self.subTest(href=href):
                body = f'<h1>Gel real</h1><div class="pd-compra"><p class="pd-preco">R$ 49,90</p><a rel="sponsored" href="{href}">Conferir na loja</a></div>'
                offer = self.one(self.graph(body, path="/produtos/gel/", article=False), "Product")["offers"]
                self.assertEqual(offer, {"@type": "Offer", "price": "49.90", "priceCurrency": "BRL"})

    def test_existing_article_is_not_duplicated(self):
        existing = {"@context": "https://schema.org", "@type": ["Article", "CreativeWork"], "@id": SITE + "/blog/teste/#artigo", "headline": "Artigo existente"}
        graph = self.graph('<h1>Artigo existente</h1>', head='<script type="application/ld+json">' + json.dumps(existing) + '</script>')
        self.assertFalse(any(n["@type"] == "Article" for n in graph))
        self.assertEqual(self.one(graph, "WebPage")["mainEntity"], {"@id": existing["@id"]})

    def test_safe_script_and_no_fictitious_contact(self):
        payload = {"name": '</script><script>alert("x")</script> & texto'}
        encoded = json_script(payload)
        self.assertNotIn("</script", encoded)
        self.assertEqual(json.loads(encoded), payload)
        graph = self.graph('<h1>Contato</h1>', path="/contato/", article=False)
        self.assertEqual(self.one(graph, "ContactPage")["url"], SITE + "/contato/")
        self.assertFalse({"email", "telephone", "address"} & self.one(graph, "Organization").keys())


if __name__ == "__main__":
    unittest.main()

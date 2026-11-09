"""Adversarial tests of the independent validator, using official vocabulary.

python -I _scripts/test_validar_schema.py --vocab PATH_TO_OFFICIAL_JSONLD
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("independent_validator", Path(__file__).with_name("validar_schema.py"))
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
VOCAB = None
SITE = validator.SITE
BODY = '<main><h1>Guia de cuidado</h1><p class="byline">Por Equipe Produto Skincare · Atualizado em <time datetime="2026-11-04">4 de novembro de 2026</time></p><p>Texto visível sobre cuidado diário.</p><img src="/foto.jpg" alt="Cuidado"></main>'


class SchemaValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skincare-schema-test-")
        self.root = Path(self.temp.name).resolve()
        (self.root / "foto.jpg").write_bytes(b"test-image-fixture")

    def tearDown(self):
        self.temp.cleanup()

    def article(self):
        return {"@context": "https://schema.org", "@type": "Article", "headline": "Guia de cuidado", "inLanguage": "pt-BR", "image": SITE + "/foto.jpg", "author": {"@type": "Organization", "name": "Equipe Produto Skincare"}, "dateModified": "2026-11-04"}

    def write_page(self, data=None, body=BODY, language="pt-BR", raw=None, extra_head=""):
        ld = raw if raw is not None else json.dumps(data or self.article(), ensure_ascii=False)
        text = '<!doctype html><html lang="' + language + '"><head><title>Teste</title><link rel="canonical" href="' + SITE + '/"><script type="application/ld+json">' + ld + '</script>' + extra_head + '</head><body>' + body + '</body></html>'
        (self.root / "index.html").write_text(text, encoding="utf-8")
        return text

    def run_audit(self, baseline=None):
        return validator.Audit(self.root, VOCAB).run(baseline)

    def codes(self, baseline=None):
        return {error["code"] for error in self.run_audit(baseline)["errors"]}

    def test_valid_factual_article(self):
        self.write_page()
        self.assertEqual(self.run_audit()["errors"], [])

    def test_rejects_malformed_json(self):
        self.write_page(raw='{"@type":"Article",}')
        self.assertIn("JSON_SYNTAX", self.codes())

    def test_rejects_duplicate_json_key(self):
        self.write_page(raw='{"@context":"https://schema.org","@type":"Article","headline":"A","headline":"B"}')
        self.assertIn("JSON_SYNTAX", self.codes())

    def test_rejects_non_finite_json_number(self):
        self.write_page(raw='{"@context":"https://schema.org","@type":"Product","offers":{"price":NaN}}')
        self.assertIn("JSON_SYNTAX", self.codes())

    def test_rejects_wrong_language(self):
        data = self.article()
        data["inLanguage"] = "en"
        self.write_page(data)
        self.assertIn("CONTENT_LANGUAGE", self.codes())

    def test_rejects_truncated_headline(self):
        data = self.article()
        data["headline"] = "Guia"
        self.write_page(data)
        self.assertIn("ARTICLE_HEADLINE", self.codes())

    def test_rejects_generic_og_image_even_if_file_exists(self):
        (self.root / "social.jpg").write_bytes(b"generic-social-image")
        data = self.article()
        data["image"] = SITE + "/social.jpg"
        self.write_page(data)
        self.assertIn("VISIBLE_IMAGE", self.codes())

    def test_rejects_hidden_image_as_visible_evidence(self):
        self.write_page(body=BODY.replace('<img src="/foto.jpg" alt="Cuidado">', '<div hidden><img src="/foto.jpg" alt="Cuidado"></div>'))
        self.assertIn("VISIBLE_IMAGE", self.codes())

    def test_rejects_fabricated_author(self):
        data = self.article()
        data["author"] = {"@type": "Person", "name": "Dra. Inventada"}
        self.write_page(data)
        self.assertIn("VISIBLE_AUTHOR", self.codes())

    def test_author_mentioned_in_body_is_not_a_byline(self):
        body = '<main><h1>Guia de cuidado</h1><p>Referência: Equipe Produto Skincare.</p></main>'
        data = self.article()
        data.pop("image")
        data.pop("dateModified")
        self.write_page(data, body)
        self.assertIn("VISIBLE_AUTHOR", self.codes())

    def test_rejects_fabricated_publication_date(self):
        data = self.article()
        data["datePublished"] = "2026-11-04"
        self.write_page(data)
        self.assertIn("VISIBLE_DATE", self.codes())

    def test_rejects_invalid_calendar_date(self):
        data = self.article()
        data["dateModified"] = "2026-02-31"
        self.write_page(data)
        self.assertIn("DATE_ISO", self.codes())

    def test_published_does_not_prove_modified(self):
        data = self.article()
        self.write_page(data, BODY.replace("Atualizado em", "Publicado em"))
        self.assertIn("VISIBLE_DATE", self.codes())

    def test_separate_dates_in_one_paragraph_do_not_cross(self):
        body = '<h1>Guia de cuidado</h1><p>Publicado em <time datetime="2026-11-02">2 de novembro de 2026</time> · Atualizado em <time datetime="2026-11-04">4 de novembro de 2026</time></p>'
        data = self.article()
        data.pop("author")
        data.pop("image")
        data["datePublished"] = "2026-11-04"
        self.write_page(data, body)
        self.assertIn("VISIBLE_DATE", self.codes())

    def test_english_dates_and_team_are_supported(self):
        body = '<h1>Care guide</h1><p>By the Produto Skincare team · Updated on <time datetime="2026-11-04">November 4, 2026</time></p><p>Published on November 2, 2026</p>'
        data = self.article()
        data.update(headline="Care guide", inLanguage="en", datePublished="2026-11-02")
        data.pop("image")
        self.write_page(data, body, "en")
        self.assertEqual(self.run_audit()["errors"], [])

    def test_spanish_dates_and_team_are_supported(self):
        body = '<h1>Guía de cuidado</h1><p>Por el equipo de Produto Skincare · Actualizado el <time datetime="2026-11-04">4 de noviembre de 2026</time></p><p>Publicado el 2 de noviembre de 2026</p>'
        data = self.article()
        data.update(headline="Guía de cuidado", inLanguage="es", datePublished="2026-11-02")
        data.pop("image")
        self.write_page(data, body, "es")
        self.assertEqual(self.run_audit()["errors"], [])

    def product(self):
        return {"@context": "https://schema.org", "@type": "Product", "name": "Sérum real", "description": "Descrição real.", "brand": {"@type": "Brand", "name": "Marca real"}, "offers": {"@type": "Offer", "price": "49.90", "priceCurrency": "BRL", "url": "https://loja.example/produto"}}

    def product_body(self):
        return '<h1>Sérum real</h1><p>Marca real</p><p>Descrição real.</p><p class="pd-preco">R$ 49,90</p><a href="https://loja.example/produto">Ver na loja</a>'

    def test_valid_product_uses_actual_price(self):
        self.write_page(self.product(), self.product_body())
        self.assertEqual(self.run_audit()["errors"], [])

    def test_rejects_price_different_from_body(self):
        data = self.product()
        data["offers"]["price"] = "9.90"
        self.write_page(data, self.product_body())
        self.assertIn("VISIBLE_PRODUCT_PRICE", self.codes())

    def test_rejects_marketplace_as_seller(self):
        data = self.product()
        data["offers"]["seller"] = {"@type": "Organization", "name": "Amazon"}
        self.write_page(data, self.product_body() + '<p>Ver na Amazon</p>')
        self.assertIn("VISIBLE_SELLER", self.codes())

    def test_rejects_unknown_property(self):
        data = self.article()
        data["imaginaryField"] = "value"
        self.write_page(data)
        self.assertIn("KNOWN_PROPERTY", self.codes())

    def test_rejects_contextless_json(self):
        data = self.article()
        data.pop("@context")
        self.write_page(data)
        self.assertIn("JSON_CONTEXT", self.codes())

    def test_rejects_property_on_wrong_class(self):
        data = self.article()
        data["price"] = "10.00"
        self.write_page(data)
        self.assertIn("PROPERTY_DOMAIN", self.codes())

    def test_rejects_wrong_object_range(self):
        data = self.article()
        data["author"] = {"@type": "Product", "name": "Guia de cuidado"}
        self.write_page(data)
        self.assertIn("PROPERTY_RANGE", self.codes())

    def test_resolves_typed_id_across_nodes(self):
        article = self.article()
        article.pop("@context")
        article["author"] = {"@id": SITE + "/#team"}
        data = {"@context": "https://schema.org", "@graph": [{"@type": "Organization", "@id": SITE + "/#team", "name": "Equipe Produto Skincare"}, article]}
        self.write_page(data)
        self.assertEqual(self.run_audit()["errors"], [])

    def test_breadcrumb_url_string_is_a_thing_reference(self):
        data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"}]}
        self.write_page(data)
        self.assertEqual(self.run_audit()["errors"], [])

    def test_rejects_unresolved_internal_id(self):
        data = self.article()
        data["author"] = {"@id": SITE + "/#missing"}
        self.write_page(data)
        self.assertIn("RESOLVED_ID", self.codes())

    def test_rejects_conflicting_id_definition(self):
        data = {"@context": "https://schema.org", "@graph": [{"@type": "Organization", "@id": SITE + "/#team", "name": "Primeiro"}, {"@type": "Organization", "@id": SITE + "/#team", "name": "Segundo"}]}
        self.write_page(data)
        self.assertIn("ID_CONFLICT", self.codes())

    def test_rejects_missing_local_url(self):
        data = self.article()
        data["url"] = SITE + "/missing/"
        self.write_page(data)
        self.assertIn("LOCAL_URL_EXISTS", self.codes())

    def test_checks_json_ld_outside_head(self):
        body = BODY + '<script type="application/ld+json">{"broken":}</script>'
        self.write_page(body=body)
        self.assertIn("JSON_SYNTAX", self.codes())

    def test_hidden_faq_answer_cannot_supply_evidence(self):
        data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Pergunta?", "acceptedAnswer": {"@type": "Answer", "text": "Resposta escondida."}}]}
        self.write_page(data, '<h1>Pergunta?</h1><p hidden>Resposta escondida.</p>')
        self.assertIn("VISIBLE_ANSWER", self.codes())

    def test_collapsed_details_answer_counts_as_available_content(self):
        data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Pergunta?", "acceptedAnswer": {"@type": "Answer", "text": "Resposta disponível."}}]}
        self.write_page(data, '<details><summary>Pergunta?</summary><p>Resposta disponível.</p></details>')
        self.assertEqual(self.run_audit()["errors"], [])

    def make_baseline(self):
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Schema test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def test_schema_only_edit_preserves_design(self):
        data = {"@context": "https://schema.org", "@type": "WebPage", "name": "Before", "inLanguage": "pt-BR"}
        self.write_page(data)
        self.make_baseline()
        data["name"] = "After"
        self.write_page(data)
        self.assertNotIn("DESIGN_BODY_UNCHANGED", self.codes("HEAD"))

    def test_rejects_body_change_against_baseline(self):
        self.write_page()
        self.make_baseline()
        self.write_page(body=BODY.replace("cuidado diário", "produto inventado"))
        self.assertIn("DESIGN_BODY_UNCHANGED", self.codes("HEAD"))

    def test_rejects_style_change_against_baseline(self):
        self.write_page(extra_head='<style>body{color:black}</style>')
        self.make_baseline()
        self.write_page(extra_head='<style>body{color:red}</style>')
        self.assertIn("DESIGN_INLINE_STYLE_UNCHANGED", self.codes("HEAD"))

    def test_rejects_runtime_js_change_against_baseline(self):
        self.write_page()
        (self.root / "ui.js").write_text("const a=1;", encoding="utf-8")
        self.make_baseline()
        (self.root / "ui.js").write_text("const a=2;", encoding="utf-8")
        self.assertIn("DESIGN_ASSET_UNCHANGED", self.codes("HEAD"))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(add_help=False)
    cli.add_argument("--vocab", type=Path, required=True)
    args, remaining = cli.parse_known_args()
    VOCAB = validator.Vocabulary(json.loads(args.vocab.read_text(encoding="utf-8")))
    unittest.main(argv=[sys.argv[0], *remaining])

"""Independent, read-only JSON-LD audit for the public static site.

Uses only Python's standard library and the official Schema.org JSON-LD
vocabulary supplied with --vocab. It does not import the schema generator.
Schema.org correctness and visible-content checks are separate from Google's
rich-result eligibility. No network requests or production mutations occur.
"""
from __future__ import annotations

import argparse
import collections
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit

SITE = "https://produtoskincare.com.br"
EXCLUDED = {".git", "_arquivo", "_scripts", "_servidor", "fotos", "fonts", "img", "icones", "node_modules"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
NONCONTENT = {"script", "style", "head", "template"}
BLOCKS = {"article", "aside", "blockquote", "button", "dd", "details", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "header", "hr", "li", "main", "nav", "ol", "p", "section", "summary", "table", "td", "th", "tr", "ul"}
LD_RE = re.compile(r'<script\b(?=[^>]*\btype\s*=\s*[\"\']application/ld\+json[\"\'])[^>]*>.*?</script\s*>', re.I | re.S)
MONTHS = {name: number for number, names in enumerate([
    ("janeiro", "january", "enero"), ("fevereiro", "february", "febrero"),
    ("março", "march", "marzo"), ("abril", "april"), ("maio", "may", "mayo"),
    ("junho", "june", "junio"), ("julho", "july", "julio"), ("agosto", "august"),
    ("setembro", "september", "septiembre"), ("outubro", "october", "octubre"),
    ("novembro", "november", "noviembre"), ("dezembro", "december", "diciembre")], 1) for name in names}
DATE_LABELS = {
    "datePublished": r"(?:Publicado\s+em|Published\s+on|Publicado\s+el)",
    "dateModified": r"(?:Atualizado\s+em|Updated\s+on|Actualizado\s+el)",
}
URL_FIELDS = {"url", "image", "logo", "thumbnailUrl", "contentUrl", "embedUrl", "sameAs", "mainEntityOfPage", "license", "acquireLicensePage"}
IDENTIFIER_FIELDS = {"gtin", "gtin8", "gtin12", "gtin13", "gtin14", "mpn", "sku"}


def norm(value):
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def words(value):
    return norm(re.sub(r"[^\w]+", " ", norm(value).casefold(), flags=re.U))


def as_list(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def local_name(value):
    for prefix in ("https://schema.org/", "http://schema.org/", "schema:"):
        if isinstance(value, str) and value.startswith(prefix):
            return value[len(prefix):]
    return value


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


class Node:
    def __init__(self, tag="document", attrs=None, parent=None, line=1):
        self.tag, self.attrs, self.parent, self.line = tag, dict(attrs or []), parent, line
        self.children = []

    def hidden(self):
        return "hidden" in self.attrs or bool(re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", self.attrs.get("style", ""), re.I))

    def visible(self):
        node = self
        while node:
            if node.hidden() or node.tag in NONCONTENT:
                return False
            node = node.parent
        return True

    def text_before(self, target):
        result = ""
        for child in self.children:
            if child is target:
                return result, True
            if isinstance(child, Node):
                text, found = child.text_before(target)
                if found:
                    return result + text, True
                result += child.text()
            else:
                result += child
        return result, False

    def text(self, visible=True):
        if visible and (self.tag in NONCONTENT or self.hidden()):
            return ""
        result = "".join(c.text(visible) if isinstance(c, Node) else c for c in self.children)
        return " " + result + " " if visible and self.tag in BLOCKS else result

    def all(self, tag=None, cls=None):
        for child in self.children:
            if isinstance(child, Node):
                if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get("class", "").split()):
                    yield child
                yield from child.all(tag, cls)

    def signature(self):
        if self.tag == "script" and self.attrs.get("type", "").casefold() == "application/ld+json":
            return None
        children = []
        for child in self.children:
            item = child.signature() if isinstance(child, Node) else norm(child)
            if item not in (None, ""):
                children.append(item)
        return [self.tag, sorted(self.attrs.items()), children]


class Document(HTMLParser):
    def __init__(self, raw, path, site=SITE):
        super().__init__(convert_charrefs=True)
        self.raw, self.path, self.site = raw, Path(path), site
        self.root = Node()
        self.stack = [self.root]
        self.feed(raw)
        self.close()
        self.body = next(self.root.all("body"), self.root)
        self.lang = next(self.root.all("html"), Node()).attrs.get("lang", "")
        self.visible = norm(self.body.text())
        self.visible_words = words(self.visible)
        self.h1 = norm(next(self.body.all("h1"), Node()).text())
        self.canonical = next((n.attrs.get("href", "") for n in self.root.all("link") if n.attrs.get("rel") == "canonical"), "")
        rel = self.path.as_posix()
        self.url = self.canonical or site + ("/" if rel == "index.html" else "/" + (rel[:-10] if rel.endswith("index.html") else rel))
        self.anchors = {self.resolve(n.attrs["href"]) for n in self.body.all("a") if n.attrs.get("href")}
        self.images = set()
        for node in self.body.all("img"):
            if not node.visible():
                continue
            if node.attrs.get("src"):
                self.images.add(self.resolve(node.attrs["src"]))
            for entry in node.attrs.get("srcset", "").split(","):
                if entry.strip():
                    self.images.add(self.resolve(entry.strip().split()[0]))
        self.video_urls = {self.resolve(n.attrs["src"]) for n in self.body.all() if n.tag in {"video", "source"} and n.attrs.get("src")}
        self.posters = {self.resolve(n.attrs["poster"]) for n in self.body.all("video") if n.attrs.get("poster")}

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag == "br":
            node.children.append(" ")
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def resolve(self, value):
        return urljoin(self.url if hasattr(self, "url") else self.site + "/", html.unescape(value))

    def facts_contain(self, value):
        wanted = words(value)
        return bool(wanted) and wanted in self.visible_words

    def dates(self, key):
        label = DATE_LABELS[key]
        found = set()
        # A datetime attribute is accepted only when its visible container labels
        # the date with the appropriate publication/update meaning.
        for node in self.body.all("time"):
            if not node.visible():
                continue
            parent = node.parent
            while parent and parent.tag not in {"body", "document"}:
                context, present = parent.text_before(node)
                if present and re.search(label + r"\s*$", norm(context), re.I) and node.attrs.get("datetime"):
                    value = node.attrs["datetime"]
                    if iso_date(value):
                        found.add(value[:10])
                    break
                parent = parent.parent
        for match in re.finditer(label + r"\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", self.visible, re.I):
            month = MONTHS.get(match[2].casefold())
            if month:
                try:
                    found.add(date(int(match[3]), month, int(match[1])).isoformat())
                except ValueError:
                    pass
        for match in re.finditer(label + r"\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})", self.visible, re.I):
            month = MONTHS.get(match[1].casefold())
            if month:
                try:
                    found.add(date(int(match[3]), month, int(match[2])).isoformat())
                except ValueError:
                    pass
        for match in re.finditer(label + r"\s+(\d{4}-\d{2}-\d{2})", self.visible, re.I):
            if iso_date(match[1]):
                found.add(match[1])
        return found

    def byline_supports(self, name):
        team_names = {"equipe produto skincare", "produto skincare team", "equipo de produto skincare", "produto skincare"}
        candidates = [norm(node.text()) for node in self.body.all() if node.visible() and node.tag in {"p", "span", "small", "address", "div"}]
        if words(name) in team_names:
            patterns = [r"^Por\s+(?:a\s+)?Equipe\s+Produto\s+Skincare\b", r"^By\s+(?:the\s+)?Produto\s+Skincare\s+team\b", r"^Por\s+el\s+equipo\s+de\s+Produto\s+Skincare\b"]
            return any(re.search(pattern, candidate, re.I) for pattern in patterns for candidate in candidates)
        return any(re.search(r"^(?:Por|By)\s+" + re.escape(norm(name)) + r"(?:\s*[·|]|$)", candidate, re.I) for candidate in candidates)


def iso_date(value):
    if not isinstance(value, str):
        return False
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            date.fromisoformat(value)
        elif re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            return False
        return True
    except ValueError:
        return False


class Vocabulary:
    def __init__(self, data):
        self.terms = {local_name(item["@id"]): item for item in data["@graph"] if item.get("@id", "").startswith(("schema:", "https://schema.org/", "http://schema.org/"))}
        self.classes = {name for name, item in self.terms.items() if "rdfs:Class" in as_list(item.get("@type"))}
        self.properties = {name for name, item in self.terms.items() if "rdf:Property" in as_list(item.get("@type"))}
        self._ancestor_cache = {}

    def links(self, term, key):
        return {local_name(x.get("@id")) for x in as_list(self.terms.get(term, {}).get(key)) if isinstance(x, dict)}

    def ancestors(self, term):
        if term not in self._ancestor_cache:
            seen, pending = {term}, [term]
            while pending:
                current = pending.pop()
                for parent in self.links(current, "rdfs:subClassOf"):
                    if parent not in seen:
                        seen.add(parent)
                        pending.append(parent)
            self._ancestor_cache[term] = seen
        return self._ancestor_cache[term]

    def is_a(self, typ, expected):
        return expected in self.ancestors(typ)

    def individual_types(self, identifier):
        item = self.terms.get(local_name(identifier), {})
        return {local_name(t) for t in as_list(item.get("@type")) if local_name(t) in self.classes}


def iter_nodes(value, pointer="$", inherited_context=None):
    if isinstance(value, dict):
        yield pointer, value, value.get("@context", inherited_context)
        for key, nested in value.items():
            if key != "@context":
                yield from iter_nodes(nested, pointer + "." + key, value.get("@context", inherited_context))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from iter_nodes(nested, pointer + "[" + str(index) + "]", inherited_context)


def comparable_url(value):
    parts = urlsplit(html.unescape(value))
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in {"tag", "linkCode", "ascsubtag"} and not k.startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, unquote(parts.path).rstrip("/"), urlencode(query), parts.fragment))


class Audit:
    def __init__(self, root, vocabulary, site=SITE):
        self.root = Path(root).resolve()
        self.vocab, self.site = vocabulary, site.rstrip("/")
        self.errors, self.warnings, self.documents, self.blocks, self.registry = [], [], [], [], {}
        self.type_counts, self.check_counts = collections.Counter(), collections.Counter()

    def issue(self, code, doc, location, message, warning=False):
        (self.warnings if warning else self.errors).append({"code": code, "file": doc.path.as_posix() if isinstance(doc, Document) else str(doc), "location": location, "message": message})

    def check(self, condition, code, doc, location, message):
        self.check_counts[code] += 1
        if not condition:
            self.issue(code, doc, location, message)
        return condition

    def read(self):
        files = sorted(p for p in self.root.rglob("*.html") if p.name in {"index.html", "404.html"} and not (set(p.relative_to(self.root).parts[:-1]) & EXCLUDED))
        for path in files:
            relative = path.relative_to(self.root)
            try:
                doc = Document(path.read_text(encoding="utf-8"), relative, self.site)
            except (UnicodeError, OSError) as error:
                self.issue("HTML_READ", relative, "", str(error))
                continue
            self.documents.append(doc)
            scripts = [n for n in doc.root.all("script") if n.attrs.get("type", "").casefold() == "application/ld+json"]
            for index, script in enumerate(scripts, 1):
                location = "script:" + str(index) + ":line:" + str(script.line)
                try:
                    data = json.loads(script.text(False), object_pairs_hook=no_duplicate_keys, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("invalid JSON constant: " + x)))
                except (ValueError, json.JSONDecodeError) as error:
                    self.issue("JSON_SYNTAX", doc, location, str(error))
                    continue
                if not isinstance(data, (dict, list)):
                    self.issue("JSON_ROOT", doc, location, "JSON-LD root must be an object or array")
                    continue
                self.blocks.append((doc, location, data))
                for pointer, node, context in iter_nodes(data):
                    self.register(doc, location + pointer, node)
            if not scripts and doc.path.name != "404.html":
                self.issue("NO_JSON_LD", doc, "", "Public index page has no JSON-LD")
        return self

    def register(self, doc, location, node):
        identifier = node.get("@id")
        if not isinstance(identifier, str) or len(node) == 1:
            return
        definition = {k: v for k, v in node.items() if k not in {"@context", "@graph"}}
        if identifier not in self.registry:
            self.registry[identifier] = {"data": definition, "origins": [(doc.path.as_posix(), location)]}
            return
        existing = self.registry[identifier]
        for key, value in definition.items():
            if key in existing["data"] and existing["data"][key] != value:
                self.issue("ID_CONFLICT", doc, location + "." + key, "Conflicting definition of " + identifier + "; first defined in " + existing["origins"][0][0])
            else:
                existing["data"][key] = value
        existing["origins"].append((doc.path.as_posix(), location))

    def resolved(self, value):
        if isinstance(value, dict) and value.get("@id") in self.registry:
            return {**self.registry[value["@id"]]["data"], **value}
        return value

    def types(self, value):
        value = self.resolved(value)
        if isinstance(value, dict):
            found = {local_name(x) for x in as_list(value.get("@type")) if isinstance(x, str)}
            if not found and isinstance(value.get("@id"), str):
                found = self.vocab.individual_types(value["@id"])
            return found
        if isinstance(value, str):
            return self.vocab.individual_types(value)
        return set()

    def url(self, value, doc, location):
        if not isinstance(value, str):
            self.issue("ABSOLUTE_URL", doc, location, "URL or @id must be a string")
            return
        parsed = urlsplit(value)
        self.check(parsed.scheme in {"https", "http"} and bool(parsed.netloc), "ABSOLUTE_URL", doc, location, "Expected absolute HTTP(S) URL: " + value)
        if parsed.hostname != urlsplit(self.site).hostname:
            return
        relative = unquote(parsed.path).lstrip("/")
        target = (self.root / relative).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            self.issue("LOCAL_URL_ESCAPE", doc, location, value)
            return
        if parsed.path.endswith("/") or not relative:
            target /= "index.html"
        elif target.is_dir():
            target /= "index.html"
        self.check(target.is_file(), "LOCAL_URL_EXISTS", doc, location, "Missing local URL target: " + value)

    def range_ok(self, value, ranges):
        if not ranges:
            return True
        if isinstance(value, dict):
            if "@value" in value:
                return self.range_ok(value["@value"], ranges)
            types = self.types(value)
            if types:
                return any(self.vocab.is_a(typ, expected) for typ in types for expected in ranges)
            # A URL-valued reference to an external entity can be opaque. Internal
            # named entity references are separately required to resolve globally.
            return bool(value.get("@id")) and ("URL" in ranges or "Thing" in ranges)
        if isinstance(value, bool):
            return "Boolean" in ranges
        if isinstance(value, (int, float)):
            return "Number" in ranges or ("Integer" in ranges and isinstance(value, int)) or "Text" in ranges
        if isinstance(value, str):
            enum_types = self.vocab.individual_types(value)
            if enum_types and any(self.vocab.is_a(typ, expected) for typ in enum_types for expected in ranges):
                return True
            # Schema.org's JSON-LD context interprets breadcrumb item URL strings
            # as IRIs identifying Things; Google documents this shorthand too.
            if "Thing" in ranges and urlsplit(value).scheme in {"https", "http"} and urlsplit(value).netloc:
                return True
            if "Text" in ranges or "URL" in ranges:
                return True
            if ranges & {"Date", "DateTime"} and iso_date(value):
                return True
            if "Duration" in ranges and re.fullmatch(r"P(?=\d|T\d)[\dYMWDTHS.]+", value):
                return True
            if ranges & {"Number", "Integer", "Float"}:
                try:
                    Decimal(value)
                    return True
                except InvalidOperation:
                    return False
        return False

    def vocabulary_node(self, doc, location, node, context):
        if node.get("@type") and context is None:
            self.issue("JSON_CONTEXT", doc, location, "Typed JSON-LD node lacks a Schema.org context")
        if context is not None:
            self.check(context in ("https://schema.org", "https://schema.org/", "http://schema.org", "http://schema.org/"), "JSON_CONTEXT", doc, location, "Unsupported/non-Schema.org context")
        types = self.types(node)
        for typ in as_list(node.get("@type")):
            typ = local_name(typ)
            self.type_counts[str(typ)] += 1
            self.check(isinstance(typ, str) and typ in self.vocab.classes, "KNOWN_TYPE", doc, location, "Unknown Schema.org class: " + str(typ))
        if "@id" in node:
            self.url(node["@id"], doc, location + ".@id")
            if len(node) == 1 and isinstance(node["@id"], str):
                parsed = urlsplit(node["@id"])
                if parsed.hostname == urlsplit(self.site).hostname and parsed.fragment:
                    self.check(node["@id"] in self.registry, "RESOLVED_ID", doc, location, "Internal entity reference has no definition: " + node["@id"])
        for key, value in node.items():
            if key.startswith("@"):
                self.check(key in {"@context", "@type", "@id", "@graph", "@value", "@language"}, "JSON_KEYWORD", doc, location, "Unsupported JSON-LD keyword: " + key)
                continue
            prop = local_name(key)
            if not self.check(prop in self.vocab.properties, "KNOWN_PROPERTY", doc, location + "." + key, "Unknown Schema.org property: " + str(key)):
                continue
            domains = self.vocab.links(prop, "schema:domainIncludes")
            ranges = self.vocab.links(prop, "schema:rangeIncludes")
            if types and domains:
                self.check(any(self.vocab.is_a(typ, domain) for typ in types for domain in domains), "PROPERTY_DOMAIN", doc, location + "." + key, "Property " + prop + " does not apply to " + ", ".join(sorted(types)))
            for val in as_list(value):
                self.check(self.range_ok(val, ranges), "PROPERTY_RANGE", doc, location + "." + key, "Value does not match expected range: " + ", ".join(sorted(ranges)))
                if isinstance(val, str) and (prop in URL_FIELDS or ranges == {"URL"} or val.startswith(("http://", "https://"))):
                    self.url(val, doc, location + "." + key)

    def factual_node(self, doc, location, node):
        types = self.types(node)
        if not node.get("@type"):
            return
        article = any(self.vocab.is_a(t, "Article") for t in types)
        webpage = any(self.vocab.is_a(t, "WebPage") for t in types)
        product = "Product" in types
        if article or webpage:
            if "inLanguage" in node:
                self.check(node["inLanguage"] == doc.lang, "CONTENT_LANGUAGE", doc, location, "inLanguage differs from html[lang]")
            if article:
                self.check(norm(node.get("headline")) == doc.h1, "ARTICLE_HEADLINE", doc, location, "Article headline must equal the complete visible H1")
        if article or webpage or product:
            for key in DATE_LABELS:
                if key in node:
                    value = node[key]
                    self.check(iso_date(value), "DATE_ISO", doc, location + "." + key, "Expected real ISO date/date-time")
                    self.check(isinstance(value, str) and value[:10] in doc.dates(key), "VISIBLE_DATE", doc, location + "." + key, "Date lacks matching visibly labelled publication/update date")
            for author in as_list(node.get("author")):
                entity = self.resolved(author)
                name = entity.get("name", "") if isinstance(entity, dict) else str(entity)
                self.check(doc.byline_supports(name), "VISIBLE_AUTHOR", doc, location + ".author", "Author lacks matching visible byline: " + name)
        if article or product:
            for image in as_list(node.get("image")):
                resolved = self.resolved(image)
                url = resolved.get("contentUrl") or resolved.get("url") or resolved.get("@id") if isinstance(resolved, dict) else resolved
                self.check(isinstance(url, str) and comparable_url(url) in {comparable_url(x) for x in doc.images}, "VISIBLE_IMAGE", doc, location + ".image", "Image must be an actual body img/srcset, not a generic OG card")
        if product:
            self.check(norm(node.get("name")) == doc.h1, "PRODUCT_NAME", doc, location, "Product name differs from visible H1")
            if node.get("description"):
                self.check(doc.facts_contain(node["description"]), "PRODUCT_DESCRIPTION", doc, location, "Product description is not visible")
            for brand in as_list(node.get("brand")):
                entity = self.resolved(brand)
                name = entity.get("name", "") if isinstance(entity, dict) else entity
                self.check(doc.facts_contain(name), "PRODUCT_BRAND", doc, location, "Product brand is not visible")
            for key in IDENTIFIER_FIELDS:
                if key in node:
                    self.check(doc.facts_contain(node[key]), "PRODUCT_IDENTIFIER", doc, location + "." + key, "Product identifier is not visible")
            price_nodes = list(doc.body.all(cls="pd-preco"))
            prices = set()
            for price_node in price_nodes:
                for match in re.finditer(r"R\$\s*([\d.]+,\d{2})", price_node.text()):
                    prices.add(Decimal(match[1].replace(".", "").replace(",", ".")))
            for offer in as_list(node.get("offers")):
                offer = self.resolved(offer)
                if not isinstance(offer, dict):
                    continue
                try:
                    value = Decimal(str(offer.get("price")))
                except InvalidOperation:
                    value = None
                self.check(value in prices and offer.get("priceCurrency") == "BRL", "VISIBLE_PRODUCT_PRICE", doc, location + ".offers", "Offer price/currency differs from visible pd-preco in BRL")
                if "description" in offer:
                    description = offer["description"]
                    # Purchase buttons can separate the visible paragraphs used in a description.
                    paragraphs = " ".join(norm(p.text()) for p in doc.body.all("p") if p.visible())
                    supported = isinstance(description, str) and bool(words(description)) and (doc.facts_contain(description) or words(description) in words(paragraphs))
                    self.check(supported, "VISIBLE_OFFER_DESCRIPTION", doc, location + ".offers.description", "Offer description is not supported by visible content")
                if offer.get("url"):
                    self.check(comparable_url(offer["url"]) in {comparable_url(x) for x in doc.anchors}, "VISIBLE_OFFER_URL", doc, location + ".offers.url", "Offer URL is not a visible purchase link")
                    self.check(not re.search(r"/search|/s\?|lista\.mercadolivre", offer["url"]), "DIRECT_OFFER_URL", doc, location + ".offers.url", "A search-results URL is not a specific product offer")
                    host = (urlsplit(offer["url"]).hostname or "").rstrip(".")
                    site_host = (urlsplit(self.site).hostname or "").rstrip(".")
                    self.check(host != site_host and not host.endswith("." + site_host), "EXTERNAL_OFFER_URL", doc, location + ".offers.url", "Affiliate site has no checkout; Offer URL must point to an external merchant")
                if offer.get("seller"):
                    seller = self.resolved(offer["seller"])
                    seller_name = seller.get("name", "") if isinstance(seller, dict) else str(seller)
                    self.check(bool(re.search(r"(?:vendido\s+por|seller\s*:)\s*" + re.escape(seller_name), doc.visible, re.I)), "VISIBLE_SELLER", doc, location + ".offers.seller", "Marketplace/platform is not evidence of the actual seller")
                if offer.get("availability"):
                    self.check(bool(re.search(r"\b(?:em estoque|esgotado|fora de estoque|in stock|out of stock)\b", doc.visible, re.I)), "VISIBLE_STOCK", doc, location + ".offers.availability", "Availability is not visible")
            if not any(node.get(key) for key in ("offers", "review", "aggregateRating")):
                self.issue("GOOGLE_PRODUCT_ELIGIBILITY", doc, location, "Semantic Product has no supported offer or own review/rating; not eligible for Google's product snippet", warning=True)
        if types & {"AggregateRating", "Review"}:
            self.issue("OWN_REVIEW_UNVERIFIED", doc, location, "This site has no verified first-party review/rating source; third-party marketplace ratings must not be marked as its own")
        if "Question" in types:
            self.check(doc.facts_contain(node.get("name")), "VISIBLE_QUESTION", doc, location, "FAQ question is not visible")
            for answer in as_list(node.get("acceptedAnswer")):
                answer = self.resolved(answer)
                text = answer.get("text", "") if isinstance(answer, dict) else str(answer)
                self.check(doc.facts_contain(text), "VISIBLE_ANSWER", doc, location, "FAQ answer differs from visible content")
        if "ItemList" in types:
            entries = as_list(node.get("itemListElement"))
            self.check(node.get("numberOfItems", len(entries)) == len(entries), "ITEMLIST_COUNT", doc, location, "numberOfItems differs from actual entries")
            positions = []
            for entry in entries:
                entry = self.resolved(entry)
                if not isinstance(entry, dict):
                    continue
                positions.append(entry.get("position"))
                item = self.resolved(entry.get("item", entry))
                if isinstance(item, dict):
                    name, url = item.get("name", entry.get("name")), item.get("url", item.get("@id", entry.get("url")))
                    self.check(doc.facts_contain(name), "VISIBLE_LIST_NAME", doc, location, "List item name is not visible")
                    if url:
                        self.check(comparable_url(url) in {comparable_url(x) for x in doc.anchors}, "VISIBLE_LIST_URL", doc, location, "List URL is not a visible link")
            self.check(positions == list(range(1, len(entries) + 1)), "ITEMLIST_POSITIONS", doc, location, "List positions are not consecutive from one")
            rendered = list(doc.body.all(cls="mv-nome"))
            if rendered:
                self.check(len(rendered) == len(entries) and [norm(x.text()) for x in rendered] == [norm(self.resolved(x).get("name")) for x in entries], "ITEMLIST_RENDERED_ORDER", doc, location, "ItemList differs from rendered product list/order")
        if "VideoObject" in types:
            self.check(node.get("contentUrl") in doc.video_urls, "VISIBLE_VIDEO", doc, location, "Video contentUrl is not a video/source in the body")
            for thumb in as_list(node.get("thumbnailUrl")):
                self.check(thumb in doc.posters or thumb in doc.images, "VISIBLE_VIDEO_POSTER", doc, location, "Video thumbnail differs from visible poster/image")
            if "uploadDate" in node:
                self.check(iso_date(node["uploadDate"]) and node["uploadDate"][:10] in doc.dates("datePublished"), "VISIBLE_VIDEO_DATE", doc, location, "Video date is not supported by the dated page")
        if any(self.vocab.is_a(t, "SoftwareApplication") for t in types) and not (node.get("review") or node.get("aggregateRating")):
            self.issue("GOOGLE_APP_ELIGIBILITY", doc, location, "App lacks a verified own rating/review required for Google's app rich result", warning=True)

    def baseline(self, baseline):
        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, capture_output=True, check=True).stdout
        try:
            git("rev-parse", "--verify", baseline + "^{commit}")
            tracked = git("ls-tree", "-r", "--name-only", baseline).decode("utf-8").splitlines()
        except subprocess.CalledProcessError as error:
            self.issue("BASELINE_READ", "", "", error.stderr.decode("utf-8", "replace"))
            return
        by_path = {doc.path.as_posix(): doc for doc in self.documents}
        for relative in tracked:
            path = Path(relative)
            if set(path.parts[:-1]) & EXCLUDED:
                continue
            if relative in by_path:
                before = Document(git("show", baseline + ":" + relative).decode("utf-8"), path, self.site)
                after = by_path[relative]
                self.check(before.body.signature() == after.body.signature(), "DESIGN_BODY_UNCHANGED", after, "body", "Body DOM/text/attributes changed beyond removal or editing of JSON-LD")
                old_styles = [n.text(False) for n in before.root.all("style")]
                new_styles = [n.text(False) for n in after.root.all("style")]
                self.check(old_styles == new_styles, "DESIGN_INLINE_STYLE_UNCHANGED", after, "style", "Inline CSS changed")
            elif path.suffix.lower() in {".css", ".js"}:
                current = self.root / path
                self.check(current.is_file() and git("show", baseline + ":" + relative).replace(b"\r\n", b"\n") == current.read_bytes().replace(b"\r\n", b"\n"), "DESIGN_ASSET_UNCHANGED", relative, "", "Runtime CSS/JS changed")

    def run(self, baseline=None):
        self.read()
        for doc, location, data in self.blocks:
            for pointer, node, context in iter_nodes(data):
                self.vocabulary_node(doc, location + pointer, node, context)
                self.factual_node(doc, location + pointer, node)
        if baseline:
            self.baseline(baseline)
        return {
            "site": self.site, "root": str(self.root), "baseline": baseline,
            "summary": {"htmlFiles": len(self.documents), "jsonLdBlocks": len(self.blocks), "namedEntities": len(self.registry), "checks": sum(self.check_counts.values()), "errors": len(self.errors), "warnings": len(self.warnings)},
            "types": dict(sorted(self.type_counts.items())), "checksByCode": dict(sorted(self.check_counts.items())),
            "errors": self.errors, "warnings": self.warnings,
            "scope": "All public index.html plus 404.html; Schema.org vocabulary and visible static content, not a substitute for Google Rich Results Test or factual medical review.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--vocab", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline")
    args = parser.parse_args()
    raw_vocab = args.vocab.read_bytes()
    vocab = Vocabulary(json.loads(raw_vocab))
    report = Audit(args.root, vocab).run(args.baseline)
    report["vocabulary"] = {"file": str(args.vocab.resolve()), "sha256": hashlib.sha256(raw_vocab).hexdigest(), "source": "https://schema.org/version/latest/schemaorg-current-https.jsonld"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

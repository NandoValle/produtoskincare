"""JSON-LD sourced from the existing HTML, without changing visible content.

Missing facts are omitted. In particular, marketplace names are not sellers,
sharing cards are not product photographs, and a publication is not an update.
"""
import html
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK = {"p", "div", "section", "article", "main", "li", "h1", "h2", "h3", "nav", "br"}
MONTHS = {}
for names in (
    "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro",
    "january february march april may june july august september october november december",
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre",
):
    MONTHS.update({name: i + 1 for i, name in enumerate(names.split())})
LABELS = {"datePublished": r"Publicado em|Published on|Publicado el", "dateModified": r"Atualizado em|Updated on|Actualizado el"}


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs or []), parent
        self.children = []

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def visible(self):
        node = self
        while node:
            if node.tag in {"head", "script", "style", "template"} or "hidden" in node.attrs or node.attrs.get("aria-hidden") == "true":
                return False
            if re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", node.attrs.get("style", ""), re.I):
                return False
            node = node.parent
        return True

    def text(self):
        if not self.visible():
            return ""
        content = "".join(child.text() if isinstance(child, Node) else child for child in self.children)
        return " " + content + " " if self.tag in BLOCK else content

    def find(self, predicate):
        for child in self.children:
            if isinstance(child, Node):
                if predicate(child):
                    yield child
                yield from child.find(predicate)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def first(self, predicate):
        return next(self.root.find(predicate), None)


def editorial_nodes(page):
    """Only bylines/metadata, not bibliography entries or dates in JSON-LD."""
    return list(page.root.find(lambda n: n.visible() and n.tag in {"p", "div", "span"} and any(
        name in {"ig-meta", "ps-byline", "mk-meta", "sub", "sb-trilha"}
        for name in n.attrs.get("class", "").split())))


def parse_date(text, label):
    match = re.search(r"(?:" + label + r")\s+(\d{4}-\d{2}-\d{2}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4}|[A-Za-z]+\s+\d{1,2},\s*\d{4})", text, re.I)
    if not match:
        return None
    value = match.group(1).lower()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value).isoformat()
        if " de " in value:
            day, month, year = value.split(" de ")
        else:
            month, day, year = value.replace(",", "").split()
        return date(int(year), MONTHS[month], int(day)).isoformat()
    except (ValueError, KeyError):
        return None


def editorial_facts(page):
    facts = {}
    for node in editorial_nodes(page):
        text = clean(node.text())
        for prop, label in LABELS.items():
            value = parse_date(text, label)
            if value and prop not in facts:
                facts[prop] = value
        if re.search(r"(?:Por\s+(?:a\s+)?Equipe Produto Skincare|By\s+(?:the\s+)?Produto Skincare team|Por\s+(?:el\s+)?equipo de Produto Skincare)", text, re.I):
            facts["team"] = True
    return facts


def existing_entities(page):
    entities = []
    for script in page.root.find(lambda n: n.tag == "script" and n.attrs.get("type") == "application/ld+json"):
        raw = "".join(c for c in script.children if isinstance(c, str))
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("JSON-LD preexistente inválido; corrija antes de gerar SEO") from exc
        entities.extend(value if isinstance(value, list) else value.get("@graph", [value]))
    return entities


def local_page_exists(root, absolute_url, site):
    parsed = urlsplit(absolute_url)
    if parsed.netloc != urlsplit(site).netloc or parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lstrip("/")
    target = root / path
    return (target / "index.html").is_file() if not path or parsed.path.endswith("/") else target.is_file()


def breadcrumbs(page, root, canonical, site, heading, brand):
    if canonical == site + "/":
        return None
    trail = page.first(lambda n: n.tag == "nav" and n.visible() and (
        "trilha" in n.attrs.get("class", "") or n.attrs.get("aria-label", "").lower() in {"trilha", "breadcrumb", "breadcrumbs"}))
    entries = []
    if trail:
        for link in trail.find(lambda n: n.tag == "a" and n.visible() and "href" in n.attrs):
            url, name = urljoin(canonical, link.attrs["href"]), clean(link.text())
            if name and url != canonical and local_page_exists(root, url, site) and url not in [x[1] for x in entries]:
                entries.append((name, url))
        current = next(trail.find(lambda n: n.attrs.get("aria-current") == "page"), None)
        name = clean(current.text()) if current else ""
        if not name:
            parts = re.split(r"[›»]", clean(trail.text()))
            if len(parts) > 1:
                name = parts[-1].strip()
        entries.append((name or heading, canonical))
    else:
        home = page.first(lambda n: n.tag == "a" and n.visible() and urljoin(canonical, n.attrs.get("href", "")) == site + "/" and brand in clean(n.text()))
        if home:
            entries.append((brand, site + "/"))
        entries.append((heading, canonical))
    if len(entries) < 2:
        return None
    return {"@type": "BreadcrumbList", "@id": canonical + "#trilha", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": name, "item": url}
        for i, (name, url) in enumerate(entries, 1)]}


def product(page, path, canonical):
    if not re.fullmatch(r"/produtos/[^/]+/", path):
        return None
    heading = page.first(lambda n: n.tag == "h1" and n.visible())
    if not heading:
        return None
    item = {"@type": "Product", "@id": canonical + "#produto", "name": clean(heading.text()), "url": canonical,
            "mainEntityOfPage": {"@id": canonical + "#pagina"}}
    description = page.first(lambda n: n.has_class("ig-lede") and n.visible())
    if description:
        # Merchant review summaries remain in the page, not in product ratings.
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", clean(description.text())) if "★" not in s]
        if sentences:
            item["description"] = " ".join(sentences)
    metadata = page.first(lambda n: n.has_class("ig-meta") and n.visible())
    if metadata and "·" in clean(metadata.text()):
        item["brand"] = {"@type": "Brand", "name": clean(metadata.text()).split("·", 1)[0].strip()}
    purchase = page.first(lambda n: n.has_class("pd-compra") and n.visible())
    if purchase:
        price = next(purchase.find(lambda n: n.has_class("pd-preco") and n.visible()), None)
        link = next(purchase.find(lambda n: n.tag == "a" and n.visible() and "sponsored" in n.attrs.get("rel", "").split()), None)
        if price and link:
            match = re.fullmatch(r"R\$\s*([\d.]+,\d{2})", clean(price.text()))
            if match:
                try:
                    amount = Decimal(match.group(1).replace(".", "").replace(",", "."))
                except InvalidOperation:
                    amount = None
                if amount is not None and amount > 0:
                    offer = {"@type": "Offer", "price": format(amount, ".2f"), "priceCurrency": "BRL"}
                    # The publisher refers buyers to another store. Preserve the
                    # visible price date/conditions without claiming a seller,
                    # stock, price expiry, or an aggregate of unknown offers.
                    notes = [clean(n.text()) for n in purchase.find(
                        lambda n: n.has_class("ig-nota") and n.visible())]
                    if any(notes):
                        offer["description"] = " ".join(note for note in notes if note)
                    destination = urljoin(canonical, link.attrs.get("href", ""))
                    target, origin = urlsplit(destination), urlsplit(canonical)
                    host, site_host = (target.hostname or "").rstrip("."), (origin.hostname or "").rstrip(".")
                    if (target.scheme in {"http", "https"} and host
                            and host != site_host and not host.endswith("." + site_host)
                            and not re.search(r"/search|/s\?|lista\.mercadolivre", destination)):
                        offer["url"] = destination
                    item["offers"] = offer
    return item


def montar_schema(root, site, brand, path, info, source, is_article):
    """Build only the managed graph; retain independent FAQ/video/app blocks."""
    page = Page(source)
    html_node = page.first(lambda n: n.tag == "html")
    language = html_node.attrs.get("lang", "").strip() if html_node else ""
    canonical_node = page.first(lambda n: n.tag == "link" and "canonical" in n.attrs.get("rel", "").split())
    canonical = urljoin(site + path, canonical_node.attrs.get("href", "")) if canonical_node else site + path
    heading_node = page.first(lambda n: n.tag == "h1" and n.visible())
    heading = clean(heading_node.text()) if heading_node else clean(info.title)
    facts = editorial_facts(page)
    publisher = {"@type": "Organization", "@id": site + "/#org", "name": brand, "url": site + "/"}
    website = {"@type": "WebSite", "@id": site + "/#site", "url": site + "/", "name": brand, "publisher": {"@id": publisher["@id"]}}
    kind = {"/sobre/": "AboutPage", "/contato/": "ContactPage"}.get(path, "WebPage")
    current = {"@type": kind, "@id": canonical + "#pagina", "url": canonical, "name": heading,
               "isPartOf": {"@id": website["@id"]}, "publisher": {"@id": publisher["@id"]}}
    if language:
        current["inLanguage"] = language
    description = clean(info.meta.get("description"))
    if description:
        current["description"] = description
    graph = [publisher, website, current]
    for prop in LABELS:
        if prop in facts:
            current[prop] = facts[prop]
    if facts.get("team"):
        author = {"@type": "Organization", "@id": site + "/#equipe", "name": "Equipe " + brand, "url": site + "/sobre/"}
        graph.append(author)
        current["author"] = {"@id": author["@id"]}
    trail = breadcrumbs(page, root, canonical, site, heading, brand)
    if trail:
        graph.append(trail)
        current["breadcrumb"] = {"@id": trail["@id"]}
    item = product(page, path, canonical)
    if item:
        graph.append(item)
        current["mainEntity"] = {"@id": item["@id"]}
    existing = existing_entities(page)
    existing_article = next((n for n in existing if any(t in {"Article", "BlogPosting", "NewsArticle"}
        for t in (n.get("@type", []) if isinstance(n.get("@type"), list) else [n.get("@type")]))), None)
    if is_article and not existing_article:
        article = {"@type": "Article", "@id": canonical + "#artigo", "headline": heading,
                   "url": canonical, "mainEntityOfPage": {"@id": current["@id"]}, "publisher": {"@id": publisher["@id"]}}
        for key in ("inLanguage", "description", "author", "datePublished", "dateModified"):
            if key in current:
                article[key] = current[key]
        cover = page.first(lambda n: n.has_class("capa-artigo") and n.visible())
        image = next(cover.find(lambda n: n.tag == "img" and n.visible() and n.attrs.get("src")), None) if cover else None
        if image:
            image_url = urljoin(canonical, image.attrs["src"])
            if "/img/og/" not in image_url:
                article["image"] = image_url
        graph.append(article)
        current["mainEntity"] = {"@id": article["@id"]}
    elif existing_article and existing_article.get("@id"):
        current["mainEntity"] = {"@id": existing_article["@id"]}
    return {"@context": "https://schema.org", "@graph": graph}


def json_script(value):
    # Avoid terminating the HTML script element when page text contains </script>.
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

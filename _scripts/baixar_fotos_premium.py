"""Baixa a foto principal de cada anúncio da página Skincare Premium.

A imagem é a do anúncio na Amazon (a mesma vitrine que a página já lista),
guardada em img/skincare-premium/<ASIN>.jpg para a página não pedir arquivo
à Amazon a cada visita. Rode de novo se entrar ASIN novo no JSON:

    python3 -I _scripts/baixar_fotos_premium.py
"""
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
JSON = RAIZ / "skincare-premium-amazon.json"
PASTA = RAIZ / "img" / "skincare-premium"
UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36")


def pegar(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,image/avif,image/webp,image/*,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("content-type", "")


def foto_do_anuncio(asin):
    html = pegar(f"https://www.amazon.com.br/gp/aw/d/{asin}")[0].decode("utf-8", "replace")
    m = re.search(r'landingImageUrl":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
    if not m:
        m = re.search(r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9+_-]+)\._AC_[^"]+\.jpg', html)
        if not m:
            raise RuntimeError("sem imagem no anúncio")
        base = m.group(1)
    else:
        base = re.search(r"/I/([A-Za-z0-9+_-]+)\.", m.group(1)).group(1)
    url = f"https://m.media-amazon.com/images/I/{base}._AC_SL640_.jpg"
    data, tipo = pegar(url)
    if "jpeg" not in tipo and not data.startswith(b"\xff\xd8"):
        raise RuntimeError(f"não é jpeg ({tipo})")
    if len(data) < 4000:
        raise RuntimeError(f"arquivo pequeno demais ({len(data)})")
    return data


def baixar(asin):
    destino = PASTA / f"{asin}.jpg"
    if destino.exists() and destino.stat().st_size > 4000:
        return asin, "ja-existe"
    erro = None
    for tentativa in range(4):
        try:
            destino.write_bytes(foto_do_anuncio(asin))
            return asin, "ok"
        except Exception as e:
            erro = e
            time.sleep(1.2 * (tentativa + 1))
    return asin, f"falhou: {erro}"


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    produtos = json.loads(JSON.read_text(encoding="utf-8"))["produtos"]
    asins = [p["asin"] for p in produtos if p.get("asin")]
    print(f"{len(asins)} anúncios com ASIN")
    ok = falha = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futuros = [pool.submit(baixar, a) for a in asins]
        for n, fut in enumerate(as_completed(futuros), 1):
            asin, status = fut.result()
            if status.startswith("falhou"):
                falha += 1
                print(f"[{n}/{len(asins)}] {asin} {status}")
            else:
                ok += 1
                if n % 25 == 0 or status == "ok" and n < 5:
                    print(f"[{n}/{len(asins)}] {asin} {status}")
    print(f"prontas {ok}, falhas {falha}, pasta {PASTA}")


if __name__ == "__main__":
    main()

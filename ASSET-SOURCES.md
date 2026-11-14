# Photography

Homepage photos are original generated images, stored locally. They replace the earlier Pexels stock (Kaboompics, Alena Darmel, Jana Kukebal). The homepage does not credit Pexels for these files.

- `img/ritual-face.jpg` and `.webp` (1000×1333) — hero portrait: Brazilian woman applying serum with a dropper. Also the first editorial story image. Replaced 2026-11-09 (afternoon): generated in ChatGPT (OpenAI image generation) as a fictional archetype ("Iara") that resembles no real celebrity; unbranded bottles; face-skin blemishes removed with a local retouch (facexlib + frequency separation); upscaled with 4x-UltraSharp and cropped to 3:4.
- `img/skincare-editorial.jpg` (960×1280) — hero inset: hand, frosted bottle, and dropper.
- `img/cream-texture.jpg` (840×1120) — cream still life on the homepage editorial story.
- `img/tipo-oleosa.jpg` (1152×864) — Oleosa card: glossy serum on skin.
- `img/tipo-seca.jpg` (1152×864) — Seca card: thick matte ivory cream.
- `img/tipo-mista.jpg` (1152×864) — Mista card: glossy serum beside cream.
- `img/tipo-normal.jpg` (1152×864) — Normal card: thin even lotion on porcelain.

No third-party image request is made by visitors. Illustrative only: no testimonial, diagnosis, or endorsement is implied.
- Cormorant Garamond 500: https://fonts.google.com/specimen/Cormorant+Garamond. Author and SIL OFL 1.1 license included in `fonts/Cormorant-OFL.txt`; source https://github.com/google/fonts/tree/main/ofl/cormorantgaramond.
- Manrope 400 and 600: https://fonts.google.com/specimen/Manrope. Author and SIL OFL 1.1 license included in `fonts/Manrope-OFL.txt`; source https://github.com/google/fonts/tree/main/ofl/manrope.
- Font files downloaded from Google Fonts CSS API and stored locally. No third-party font request is made by visitors.

## Blog covers — generated 2026-11-04

- Files: `img/blog/<slug>-3840.webp` (4K master, 3840×2160), `-1600.webp`, `-800.webp` (responsive sizes) and `-og.jpg` (1200×675, social share preview).
- Slugs: `como-saber-tipo-de-pele`, `retinol-como-comecar`, `vitamina-c-skincare`, `protetor-solar-importancia`.
- Added 2026-11-05, same model and settings: `protetor-solar-pele-oleosa`, `ordem-dos-produtos-skincare`, `rotina-de-skincare-barata`, `protetor-solar-com-cor`, `skincare-pele-negra`, `skincare-masculino`, `skincare-para-adolescentes` (these articles keep their existing `img/og/` share images).
- Origin: AI-generated images (OpenAI GPT Image model `gpt-image-2.5-sunburst`, accessed through ElevenLabs Creative flows), 16:9, 4K, quality "high". Prompts asked for no text, no logos, no brand packaging and no people.
- Illustrative only: they do not depict any specific product sold or linked on the site, and imply no endorsement or result.
- Stored locally; no third-party image request is made by visitors.

## News videos ("a notícia em 1 minuto") — added 2026-11-09

- Files: `blog/<slug>/video.mp4` (720×1280, H.264 + AAC), `poster.jpg` and `legendas.vtt` for `anvisa-cosmetovigilancia-notificacoes-130-2026`, `revisao-antioxidantes-topicos-fotoenvelhecimento-2026` and `skincare-brasileiro-biodiversidade-identidade-2026`.
- Narration: AI-generated voice (ElevenLabs, voice "Bianca - Smooth and Sophisticated", model `eleven_v4`), reading the scripts in `_roteiros/<slug>.txt`. Captions come from the word timings of an ElevenLabs transcription (`eleven_scribe_v1`).
- Frames: text slides drawn by `_scripts/video_noticia.py` in the site's colors (slide texts in `_roteiros/<slug>.quadros.json`); no photos, logos or people.
- Stored locally; no third-party video request is made by visitors.

## News covers — generated 2026-11-09

- Files: `img/blog/<slug>-3840.webp`, `-1600.webp`, `-800.webp` and `-og.jpg` (1200×675, social share preview, now the page's `og:image`).
- Slugs: `anvisa-cosmetovigilancia-notificacoes-130-2026`, `revisao-antioxidantes-topicos-fotoenvelhecimento-2026`, `skincare-brasileiro-biodiversidade-identidade-2026`, `esteroides-nao-declarados-cremes-jama`, `unilever-foco-beleza-economia-1-bilhao`, `pele-tem-sexo-estudo-nature`, `ozempic-face-gigantes-da-beleza`.
- Origin: AI-generated images made in ChatGPT (OpenAI image generation, the site owner's account) at 1672×941, cropped to 16:9 and upscaled to 3840×2160 with the 4x-UltraSharp ESRGAN model (the 4K master is an upscale, not a native 4K render). Built by `_scripts/capa_post.py`; prompts and rules in `_roteiros/capas.txt`.
- Prompts asked for no text, no logos, no brand names, no readable labels and no identifiable faces. Products shown are generic and unbranded, even when the news is about a specific company.
- Illustrative only: they do not depict any specific product sold or linked on the site, and imply no endorsement or result.
- Stored locally; no third-party image request is made by visitors.

## Queridinhos pelo mundo — country images, added 2026-11-11

- Files: `img/queridinhos/<country>-480.webp` and `-960.webp` (square) for `eua`, `brasil`, `coreia`, `japao`, `franca`, `canada`, `alemanha`, `espanha`, shown at the top of each country section of `/queridinhos-do-skincare/` with the caption "Imagem ilustrativa, gerada por IA".
- Origin: AI-generated images. `coreia`, `japao`, `alemanha` and `espanha` were made in ChatGPT (OpenAI image generation, the site owner's account, 1254×1254). `eua`, `brasil`, `franca` and `canada` were supplied by the site owner (1024×1024); the generator was not recorded.
- They show product packaging of the brands listed in each section as rendered by an AI model. They are illustrations, not photographs of the actual products: packaging, labels and text may differ from the real items. No endorsement by the brands is implied.
- Stored locally; no third-party image request is made by visitors.

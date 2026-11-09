# Photography

Homepage photos are original generated images, stored locally. They replace the earlier Pexels stock (Kaboompics, Alena Darmel, Jana Kukebal). The homepage does not credit Pexels for these files.

- `img/ritual-face.jpg` and `.webp` (1000×1333) — hero portrait: Brazilian woman applying cream. Also the first editorial story image. Replaced 2026-11-09: generated in ChatGPT (OpenAI image generation) with a prompt asking for a fictional person who resembles no real celebrity; eye color changed afterwards to green with a local hue edit (Pillow/NumPy); cropped to 3:4.
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

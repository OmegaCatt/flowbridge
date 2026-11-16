# FlowBridge: video ukázka

**[Stáhnout MP4 — 0:46, bez zvuku](https://raw.githubusercontent.com/OmegaCatt/flowbridge/main/docs/videos/flowbridge.mp4)** · [Soubor na GitHubu](https://github.com/OmegaCatt/flowbridge/blob/main/docs/videos/flowbridge.mp4)

HTTP přenos do testovacího CRM, ochrana před duplicitou a opakování po chybě potvrzení.

## Co ve videu uvidíte

- Náhled bez zápisu a skutečný HTTP přenos do místního testovacího CRM.
- Opakování stejné události bez duplicitního záznamu.
- Ztracené potvrzení po zápisu, HTTP 503 a úspěšný druhý pokus.

Video zachycuje skutečnou aplikaci nad izolovanými fiktivními daty. Má rozlišení **1920 × 1080**, **25 snímků/s**, přibližně **2.7 MB** a české titulky přímo v obrazu. Pohyb myši i kliknutí jsou viditelné. **Neobsahuje zvukovou stopu.**

Odkaz stáhne video MP4. Po stažení jej otevřete v běžném přehrávači videa. Ukázka nepotřebuje instalaci aplikace. Pro vlastní vyzkoušení pokračujte [návodem ke spuštění](../README.md#spuštění-krok-za-krokem-windows).

## Jak byl záznam ověřen

Při pořizování proběhl skutečný HTTP/browser scénář s kontrolami výsledků. AI API nebylo volané. Ověřeno celé dekódování výsledného MP4, H.264/yuv420p, rozlišení, absence audio stopy, samostatné přehrání/posun a obrazové snímky titulkových úseků a kliknutí. Jde o ověření konkrétní ukázky; záznam neměří obecnou přesnost AI ani produkční připravenost aplikace.

[Metadata záznamu](videos/flowbridge-recording.json) obsahují kontrolované výsledky, zdrojový commit `71ef9e816f1b3c8c50c3cb03e296c5e601634fc7` a otisky nahrávacích skriptů. SHA-256 MP4: `592985d3a4edc00a21e09068d45eab88c15a3d5f37779532074266ffe40117c7`. Časy kroků v metadatech jsou orientační; titulky jsou přímo v obrazu.

Scénář: [scripts/record-demo.mjs](../scripts/record-demo.mjs). Nahrávací vrstva: [scripts/recording.mjs](../scripts/recording.mjs). Při vývojovém zopakování je potřeba Playwright a plný FFmpeg s libx264 (`PORTFOLIO_FFMPEG`); běžné přehrání videa je nevyžaduje.

## English

**[Download the silent Full HD demo (0:46)](https://raw.githubusercontent.com/OmegaCatt/flowbridge/main/docs/videos/flowbridge.mp4).** Open the downloaded MP4 in a standard video player. Czech captions are burned into the image; the pointer and actual clicks are visible. Recorded from the real application using isolated fictional data, with result assertions and no AI API calls. Full decoding, playback, seeking and absence of audio were verified. [Run the application locally](../README.md#spuštění-krok-za-krokem-windows).

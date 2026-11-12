# Snadné vyzkoušení - 12. 11. 2026

Základní Windows návod je na začátku README; řešení potíží a volitelné předpoklady v docs/SPUSTENI.md. Netechnický návštěvník může začít existující veřejnou ukázkou. Ověření čisté kopie a hranice testu jsou v docs/QA.md. Jádro aplikace se touto dokumentační úpravou nemění.

# UX-1 až UX-7 – 11. 11. 2026

Doplněná úvodní nápověda a stručné technické vysvětlení v hlavičce. Integrační engine této UI etapy se nemění.

Všech sedm aplikací má první přístupný dialog a stálé ovládání nápovědy v hlavičce. Playwright ověřuje skutečný první vstup, obě části, GitHub odkaz, Tab/Shift+Tab, Escape, návrat fokusu, potvrzení po reloadu a mobil. CompanyAtlas čeká s přihlášením na zavření úvodu; hlavička se testuje po přihlášení. Legacy pracovní průchody pokračují po skutečném zavření úvodu. Aktuální commit, CI a přesný rozsah ověření této etapy jsou vedené v hlavním Portfolio_PROGRESS.md; starší zápisy níže jsou historické.

# Aktuální rozsah a kontrola 10. 11. 2026

Aktuální funkce, technologie, API, způsob použití, firemní zavedení a omezení jsou v [README](../README.md). Znovu prošlo 13 Python testů a odpovídající skutečný browser průchod desktop/mobil. Jde o fiktivní portfolio projekt. Výsledky a případné opravy jsou v [QA](QA.md).

Předchozí ověřený kód 6cd6432: [úspěšné GitHub Actions](https://github.com/OmegaCatt/flowbridge/actions/runs/42731084972). Nový commit této revize má vlastní CI; aktuální stav je v hlavním protokolu portfolia. Níže uvedené historické plány nejsou seznam nehotových funkcí.

<details>
<summary>Historická projektová rozhodnutí a průběžné etapy</summary>

# Zadání a rozhodnutí

FB-1 až FB-7 podle hlavního plánu portfolia: jeden objednávkový tok, dvě skutečné testovací HTTP služby, omezená trvalá fronta a dohledání chyb. Bez univerzálního vizuálního editoru a bez AI, která pro transport nepřidává potřebnou jistotu.

Rozhodnutí: eventId identifikuje zdrojovou událost, orderId je cílový obchodní klíč. Zdrojový otisk zachovává originál včetně režimu simulace. JSON mode je pouze testovací emulace chyby. Target URL určuje server. Cílový příjem se neopírá pouze o ochranu ve zdrojové frontě. Vypršelý lease vede k opakování stejného klíče. Nejde o archiv skutečných zákaznických dat. Aktuální kontrakt, spuštění a limity jsou v README.


</details>

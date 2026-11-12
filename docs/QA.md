# Regrese DOC-5: fokus po zavření nápovědy - 12. 11. 2026

Opožděná událost close už nepřepisuje mezitím výslovně přesunutý fokus. Původní chování se prokázalo v prohlížeči: technický dialog → zavření a okamžité zaměření tlačítka používání → starý close vracel fokus na technické tlačítko. Oprava zachová nové zaměření; Enter otevře správný návod. Stejná regrese je součástí skutečných browser kontrol, původní očekávání klávesnice ani rychlého reloadu nejsou oslabená. Záložní návrat fokusu zůstává zachovaný, pokud nové zaměření neexistuje.

První neúspěšné OfferLens CI je [zachované v historii](https://github.com/OmegaCatt/offerlens/actions/runs/43320912740). Jde o omezenou opravu nápovědy, obchodní výpočty a data nemění.

# Ověření jednoduchého spuštění - 12. 11. 2026

README začíná návodem pro netechnického zájemce: stažení a rozbalení ZIP, otevření PowerShellu ve složce, přesný příkaz, adresa v prohlížeči a ukončení Ctrl+C. Vývojové testy jsou oddělené, volitelné AI/PDF požadavky popsané samostatně.

Ověřena nová kopie sledovaných zdrojů bez místních env souborů, uživatelských databází a předem instalovaného node_modules. Místní HTTP server vrátil 200 a správnou stránku aplikace. Pro zachování běžících služeb byla zvolena náhodná loopback adresa; hodnoty běžných portů v README odpovídají vstupním serverovým skriptům. ReleaseGuard doinstaloval runtime závislosti přes npm; CompanyAtlas použil nový Python venv a instalaci requirements.txt. Ostatní aplikace nepotřebují runtime balíčky pro základní ukázku.

Znovu prošlo **13 Python testů**. Běžné pracovní průchody mají samostatné prohlížečové regrese v tomto repozitáři. Toto ověření nenahrazuje kontrolu instalátoru Node/Python na každém počítači ani nepředstavuje obecnou záruku správnosti.

# Regrese UX-1b – rychlé zavření a reload

První Linux main CI odhalilo závod: potvrzení úvodu v události close se někdy nestihlo zapsat před reloadem. Nyní se zapisuje synchronně v Escape/cancel a tlačítkách před zavřením; close je záložní cesta. Původní neúspěšný běh zůstává v Actions. Browser test stále provádí okamžitý reload, očekávání nebylo oslabeno ani přidán čekací čas.

# UX-1 až UX-7 – 11. 11. 2026

První společný paralelní browser běh jednou překročil 30 s při čekání na tabulku. Dva následující samostatné běhy se zachycením skutečného HTTP přijetí prošly. Byla doplněná diagnostika QA; integrační engine nebyl v této etapě měněný.

Místně ověřené unit testy: **13 Python**.

Doplněná úvodní nápověda a stručné technické vysvětlení v hlavičce. Integrační engine této UI etapy se nemění.

Všech sedm aplikací má první přístupný dialog a stálé ovládání nápovědy v hlavičce. Playwright ověřuje skutečný první vstup, obě části, GitHub odkaz, Tab/Shift+Tab, Escape, návrat fokusu, potvrzení po reloadu a mobil. CompanyAtlas čeká s přihlášením na zavření úvodu; hlavička se testuje po přihlášení. Legacy pracovní průchody pokračují po skutečném zavření úvodu. Aktuální commit, CI a přesný rozsah ověření této etapy jsou vedené v hlavním Portfolio_PROGRESS.md; starší zápisy níže jsou historické.

# Opakované ověření 10. 11. 2026

**13 Python testů prošlo.** Znovu spuštěné prohlížečové QA ověřilo skutečný pracovní postup na dočasných fiktivních podkladech, desktop i mobil a JavaScript chyby. Nová kontrola zopakovala běžné i připravené chybové toky. Původní počet testů zůstává beze změny.

Ověřený předchozí commit 6cd6432: [GitHub Actions](https://github.com/OmegaCatt/flowbridge/actions/runs/42731084972); dostupnost jeho artefaktů byla ověřena. Aktuální revize dokumentace/oprav je kontrolována novým CI. Jeho přesný commit a výsledek jsou v hlavním Portfolio_PROGRESS.md. Staré věty o čekající publikaci v rozbaleném archivu platily jen pro dobu daného zápisu.

<details>
<summary>Historické výsledky, původní metriky a omezení</summary>

# Ověření 10. 11. 2026

13 Python unittestů prošlo na Pythonu 3.13.17: dvě skutečné HTTP služby a oddělené SQLite databáze; atomické přijetí pěti stejných událostí a jediný nárok; obnova po restartu; lease; přesné peníze; žádný zápis v náhledu; retry 503/429; 422 a validace; vyčerpání tří pokusů; dva ruční replay cykly; cílový konflikt a nezdvojený zápis po selhání potvrzení.

Browser Playwright/Edge na Node 24.22.1: náhled bez zápisu, skutečné doručení, duplicitní událost a konflikt, po-zápisové 503 a dva pokusy s jedním novým CRM záznamem, detail podkladů a JSON, vadný e-mail bez replay, filtr chyb, replay 422, desktop 1440 a mobil 390 px bez JS chyb/přetečení. Snímky preview.png, detail.png, mobile.png vizuálně zkontrolované. Pozdější regrese zneplatňuje náhled při změně vstupu. Žádné externí API nebo skutečné CRM.

Připravený CI workflow není sám důkaz vzdáleného úspěchu. Ověření konkrétního publikovaného commitu se doplní po doběhnutí Actions. Neověřujeme tím produkční kapacitu, obecné doručení právě jednou ani provozní SLA.

Regrese zadržené skutečné HTTP odpovědi náhledu: uživatel mezitím změní JSON; starý náhled se nevrátí a UI výslovně upozorní, že výsledek patřil předchozímu vstupu.

## Ověřený vzdálený běh

Kód 98cb68a prošel GitHub Actions na hlavní větvi: https://github.com/OmegaCatt/flowbridge/actions/runs/42729883848. Zahrnuje 13 Python testů, skutečné HTTP/regrese a browser QA; report se vztahuje k tomuto commitu.


</details>

# Ověření 10. 11. 2026

13 Python unittestů prošlo na Pythonu 3.13.17: dvě skutečné HTTP služby a oddělené SQLite databáze; atomické přijetí pěti stejných událostí a jediný nárok; obnova po restartu; lease; přesné peníze; žádný zápis v náhledu; retry 503/429; 422 a validace; vyčerpání tří pokusů; dva ruční replay cykly; cílový konflikt a nezdvojený zápis po selhání potvrzení.

Browser Playwright/Edge na Node 24.22.1: náhled bez zápisu, skutečné doručení, duplicitní událost a konflikt, po-zápisové 503 a dva pokusy s jedním novým CRM záznamem, detail podkladů a JSON, vadný e-mail bez replay, filtr chyb, replay 422, desktop 1440 a mobil 390 px bez JS chyb/přetečení. Snímky preview.png, detail.png, mobile.png vizuálně zkontrolované. Pozdější regrese zneplatňuje náhled při změně vstupu. Žádné externí API nebo skutečné CRM.

Připravený CI workflow není sám důkaz vzdáleného úspěchu. Ověření konkrétního publikovaného commitu se doplní po doběhnutí Actions. Neověřujeme tím produkční kapacitu, obecné doručení právě jednou ani provozní SLA.

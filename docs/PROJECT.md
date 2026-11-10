# Zadání a rozhodnutí

FB-1 až FB-7 podle hlavního plánu portfolia: jeden objednávkový tok, dvě skutečné testovací HTTP služby, omezená trvalá fronta a dohledání chyb. Bez univerzálního vizuálního editoru a bez AI, která pro transport nepřidává potřebnou jistotu.

Rozhodnutí: eventId identifikuje zdrojovou událost, orderId je cílový obchodní klíč. Zdrojový otisk zachovává originál včetně režimu simulace. JSON mode je pouze testovací emulace chyby. Target URL určuje server. Cílový příjem se neopírá pouze o ochranu ve zdrojové frontě. Vypršelý lease vede k opakování stejného klíče. Nejde o archiv skutečných zákaznických dat. Aktuální kontrakt, spuštění a limity jsou v README.

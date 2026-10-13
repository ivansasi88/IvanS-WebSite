# Home unificata: Ivan Sasi + IS Inspiration Studio

Landing page indipendente e responsive, sviluppata in HTML e CSS senza dipendenze o framework.

## Architettura
- index.html: home comune, con avatar, messaggio e due card di navigazione
- ivan-sasi/index.html: pagina Ivan Sasi / Pillole di Diabete
- studio/index.html: pagina IS Inspiration Studio
- style.css: design system condiviso e responsive

## Cloudflare Pages
Collega il repository `ivansasi88/IvanS-WebSite` tramite *Workers & Pages > Create application > Pages > Import an existing Git repository*.

Impostazioni:
- Production branch: `main`
- Root directory (advanced): `unified-home`
- Framework preset: None
- Build command: `exit 0`
- Build output directory: `.`

Una volta pubblicato, Cloudflare assegna un indirizzo `nome-progetto.pages.dev`. Il nome scelto deve essere disponibile.
La pubblicazione su Cloudflare non è eseguita da questi file: occorre autorizzare il collegamento GitHub ↔ Cloudflare dal dashboard.

## Note
- La cartella è separata dal sito GitHub Pages presente nella root del repository.
- I link interni utilizzano percorsi assoluti, corretti quando Cloudflare pubblica `unified-home` come root.
- Il ritratto è incorporato nel file HTML, ripreso dall'avatar già pubblico nel sito esistente.
- Il monogramma IS è una resa tipografica da sostituire con il file vettoriale originale del nuovo logo per la massima fedeltà.

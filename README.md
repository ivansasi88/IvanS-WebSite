# IvanS-WebSite

Sito personale (GitHub Pages). Gli APK si gestiscono da soli tramite GitHub Actions.

## Aggiungere una nuova versione di un'app
1. Copia l'APK in `downloads/<app>/` (es. `downloads/glyvia-stock/`). Il nome non conta, ma deve finire con la versione (`... 1.6.0.apk` oppure `...-v1.6.0.apk`).
2. Commit + push.
3. Dopo circa un minuto il workflow rinomina il file in `<app>-v1.6.0.apk`, tiene le 2 versioni più recenti, cancella le altre e aggiorna `downloads/manifest.json`. Il sito mostra "attuale" e "precedente".

## Aggiungere un'app nuova
1. Crea `downloads/<slug>/app.json` (copia quello di un'altra app e cambia `title`, `tag`, `description`, `icon`, `accent`, `order`).
2. Metti l'icona in `assets/` e scrivi il percorso in `icon` (senza icona compare l'iniziale).
3. Aggiungi l'APK nella stessa cartella, commit + push: la card compare da sola.

## Regole
- `manifest.json` è generato dal workflow: non modificarlo a mano.
- Un APK fuori da una cartella app, senza versione nel nome o non valido viene ignorato (vedi i warning in *Actions*).
- Se il download non parte, guarda la tab *Actions*: il workflow deve avere la spunta verde.
- Limiti GitHub: 100 MB per file (warning sopra 50 MB); ogni versione pubblicata resta nella cronologia git anche dopo la cancellazione.

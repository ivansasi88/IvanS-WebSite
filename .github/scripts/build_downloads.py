#!/usr/bin/env python3
"""
Gestisce la cartella downloads/ del sito.

Per ogni sottocartella (= una app):
  - trova gli APK e ne ricava la versione dalla parte finale del nome
  - rinomina ogni APK in <slug>-v<versione>.apk (minuscolo, senza spazi)
  - tiene solo le KEEP versioni piu' recenti (ordinamento numerico) e cancella le altre
  - legge i metadati da app.json
Poi rigenera downloads/manifest.json, che e' quello che legge la pagina.

Non fa mai fallire il job per un file "sbagliato": scrive un warning e va avanti.
Rieseguirlo senza novita' non produce nessuna modifica (idempotente).
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("DOWNLOADS_DIR", "downloads"))
KEEP = 2
MANIFEST = ROOT / "manifest.json"

# Versione = 2-4 numeri separati da punti, prefisso "v" opzionale, subito prima di ".apk".
# Tollera il suffisso " (1)" che i browser aggiungono ai file scaricati due volte.
VERSION_RE = re.compile(r"(?<![\d.])v?(\d+(?:\.\d+){1,3})(?:\s*\(\d+\))?\.apk$", re.IGNORECASE)
ACCENT_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")

DEFAULT_ACCENT = "#55d6ac"


def warn(msg):
    print(f"::warning::{msg}")


def info(msg):
    print(msg)


def vkey(version):
    """'1.5.13' -> (1, 5, 13, 0): confronto numerico, non alfabetico."""
    parts = [int(x) for x in version.split(".")]
    return tuple(parts + [0] * (4 - len(parts)))


def clean_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def looks_like_apk(path):
    """Un APK e' uno zip: deve iniziare con 'PK\\x03\\x04'."""
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"PK\x03\x04"
    except OSError:
        return False


def load_old_manifest():
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return {a["slug"]: a for a in data.get("apps", []) if "slug" in a}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def read_meta(folder, old_app):
    """Legge app.json. Se e' rotto, riusa i metadati gia' pubblicati per non far sparire la card."""
    path = folder / "app.json"
    if not path.is_file():
        warn(f"{folder.name}: manca app.json, cartella ignorata.")
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("deve essere un oggetto JSON")
    except (OSError, ValueError) as e:
        if old_app:
            warn(f"{folder.name}/app.json non valido ({e}): uso gli ultimi metadati pubblicati.")
            raw = {k: old_app.get(k) for k in ("title", "tag", "description", "icon", "accent", "order")}
        else:
            warn(f"{folder.name}/app.json non valido ({e}): cartella ignorata.")
            return None

    def text(key, default=""):
        v = raw.get(key)
        return v.strip() if isinstance(v, str) else default

    accent = text("accent", DEFAULT_ACCENT)
    if not ACCENT_RE.match(accent):
        warn(f"{folder.name}/app.json: accent '{accent}' non valido, uso {DEFAULT_ACCENT}.")
        accent = DEFAULT_ACCENT
    order = raw.get("order")
    if isinstance(order, bool) or not isinstance(order, (int, float)):
        order = 999
    return {
        "title": text("title", folder.name),
        "tag": text("tag"),
        "description": text("description"),
        "icon": text("icon"),
        "accent": accent,
        "order": order,
    }


def process_folder(folder, old_app, today):
    """Rinomina/pota gli APK della cartella e restituisce le versioni da pubblicare."""
    slug_prefix = clean_slug(folder.name)
    candidates = {}  # vkey -> lista di (path, version_string)

    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.suffix.lower() != ".apk":
            continue
        m = VERSION_RE.search(f.name)
        if not m:
            warn(f"{folder.name}/{f.name}: versione non riconosciuta nel nome, file ignorato.")
            continue
        if not looks_like_apk(f):
            warn(f"{folder.name}/{f.name}: non sembra un APK valido (file vuoto o corrotto), ignorato.")
            continue
        candidates.setdefault(vkey(m.group(1)), []).append((f, m.group(1)))

    chosen = []  # (vkey, version_string, path)
    for key, items in candidates.items():
        if len(items) > 1:
            # Vince il file NON ancora rinominato (= appena caricato), poi il piu' recente.
            def rank(item):
                p, v = item
                is_canonical = p.name == f"{slug_prefix}-v{v}.apk"
                return (not is_canonical, p.stat().st_mtime, p.name)

            items.sort(key=rank, reverse=True)
            for loser, _ in items[1:]:
                warn(f"{folder.name}: versione duplicata, tengo {items[0][0].name} ed elimino {loser.name}.")
                loser.unlink()
        path, version = items[0]
        chosen.append((key, version, path))

    chosen.sort(key=lambda t: t[0], reverse=True)

    for _, version, path in chosen[KEEP:]:
        info(f"{folder.name}: elimino la versione {version} ({path.name}), oltre le ultime {KEEP}.")
        path.unlink()
    chosen = chosen[:KEEP]

    old_versions = {(v.get("file"), v.get("sha256")): v for v in (old_app or {}).get("versions", [])}
    versions = []
    for _, version, path in chosen:
        target = folder / f"{slug_prefix}-v{version}.apk"
        if path != target:
            info(f"{folder.name}: rinomino {path.name} -> {target.name}")
            os.replace(path, target)
        rel = target.as_posix()
        digest = sha256_of(target)
        prev = old_versions.get((rel, digest))
        versions.append({
            "version": version,
            "file": rel,
            "size": target.stat().st_size,
            "sha256": digest,
            "date": prev["date"] if prev and "date" in prev else today,
        })
    return versions


def main():
    if not ROOT.is_dir():
        print(f"Cartella {ROOT} non trovata.", file=sys.stderr)
        return 1

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    old = load_old_manifest()
    apps = []

    for loose in sorted(ROOT.glob("*.apk")):
        warn(f"{loose.name}: APK fuori da una cartella app, ignorato. Mettilo in downloads/<app>/.")

    for folder in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        meta = read_meta(folder, old.get(folder.name))
        if meta is None:
            continue
        versions = process_folder(folder, old.get(folder.name), today)
        apps.append({"slug": folder.name, **meta, "versions": versions})

    apps.sort(key=lambda a: (a["order"], a["title"].lower()))
    new_text = json.dumps({"apps": apps}, indent=2, ensure_ascii=False) + "\n"

    old_text = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
    if new_text != old_text:
        MANIFEST.write_text(new_text, encoding="utf-8")
        info("manifest.json aggiornato.")
    else:
        info("manifest.json invariato.")

    for a in apps:
        latest = a["versions"][0]["version"] if a["versions"] else "nessun APK"
        info(f"  - {a['slug']}: {len(a['versions'])} versione/i (ultima: {latest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

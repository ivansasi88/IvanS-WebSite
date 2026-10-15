#!/usr/bin/env bash
set -euo pipefail

OUT=".cloudflare-dist"
LIMIT=26214400

rm -rf "$OUT"
mkdir -p "$OUT"

while IFS= read -r -d '' file; do
  rel="${file#./}"
  case "$rel" in
    .git/*|"$OUT"/*|LEGGIMI-NON-CARICARE.txt) continue ;;
  esac

  if [[ "$rel" == *.apk ]] && (( $(stat -c%s "$file") > LIMIT )); then
    continue
  fi

  destination="$OUT/$rel"
  mkdir -p "$(dirname "$destination")"
  cp "$file" "$destination"
done < <(find . -type f -print0)

: > "$OUT/_redirects"
while IFS= read -r -d '' file; do
  rel="${file#./}"
  if (( $(stat -c%s "$file") > LIMIT )); then
    printf '/%s https://raw.githubusercontent.com/ivansasi88/IvanS-WebSite/main/%s 302\n' "$rel" "$rel" >> "$OUT/_redirects"
  fi
done < <(find downloads -type f -name '*.apk' -print0)

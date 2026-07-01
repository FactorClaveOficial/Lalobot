#!/usr/bin/env bash
# Descarga el binario de PhoneInfoga (no se versiona por tamaño ~30MB).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="https://github.com/sundowndev/phoneinfoga/releases/latest/download/phoneinfoga_Linux_x86_64.tar.gz"

echo "[*] Descargando PhoneInfoga en $DIR ..."
curl -sSL -o "$DIR/pi.tar.gz" "$URL"
tar xzf "$DIR/pi.tar.gz" -C "$DIR" phoneinfoga
rm -f "$DIR/pi.tar.gz"
chmod +x "$DIR/phoneinfoga"
"$DIR/phoneinfoga" version
echo "[✓] PhoneInfoga listo en $DIR/phoneinfoga"

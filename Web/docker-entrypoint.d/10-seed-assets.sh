#!/bin/sh
set -eu

ASSETS_VOLUME_PATH="${ASSETS_VOLUME_PATH:-/usr/share/nginx/html/assets}"
ASSETS_SEED_PATH="${ASSETS_SEED_PATH:-/seed/assets}"
FORCE_ASSETS_SEED="${FORCE_ASSETS_SEED:-0}"

if [ ! -d "$ASSETS_SEED_PATH" ]; then
  echo "[seed-assets] Seed no existe: $ASSETS_SEED_PATH (omitido)"
  exit 0
fi

mkdir -p "$ASSETS_VOLUME_PATH"

echo "[seed-assets] Seed:   $ASSETS_SEED_PATH"
echo "[seed-assets] Volumen:$ASSETS_VOLUME_PATH"

# Algunos proveedores crean 'lost+found' en el root del volumen; no debe bloquear el seed.
HAS_REAL_CONTENT="$(find "$ASSETS_VOLUME_PATH" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -print -quit 2>/dev/null || true)"

if [ "$FORCE_ASSETS_SEED" = "1" ]; then
  echo "[seed-assets] FORCE_ASSETS_SEED=1; re-seed activado"
  rm -rf "$ASSETS_VOLUME_PATH"/*
  cp -a "$ASSETS_SEED_PATH/." "$ASSETS_VOLUME_PATH/"
  echo "[seed-assets] Re-seed completo. Conteo:"
  echo "[seed-assets] - dirs:  $(find "$ASSETS_VOLUME_PATH" -type d | wc -l | tr -d ' ')"
  echo "[seed-assets] - files: $(find "$ASSETS_VOLUME_PATH" -type f | wc -l | tr -d ' ')"
  for f in "images/Logo Fundo Moraga.png" "images/066D82F6-A14A-4BBC-818F-FB3411BB8D6D.JPEG" "images/Hernando.PNG" "videos/Fundo Moraga.mp4" "videos/Leyenda Fundo Moraga.mp4"; do
    if [ -f "$ASSETS_VOLUME_PATH/$f" ]; then
      echo "[seed-assets] OK: $f"
    else
      echo "[seed-assets] MISSING: $f"
    fi
  done
elif [ -z "$HAS_REAL_CONTENT" ]; then
  echo "[seed-assets] Inicializando volumen: $ASSETS_VOLUME_PATH"
  cp -a "$ASSETS_SEED_PATH/." "$ASSETS_VOLUME_PATH/"
  echo "[seed-assets] Ejemplos:"
  find "$ASSETS_VOLUME_PATH" -type f -maxdepth 3 | head -n 5 | sed 's/^/[seed-assets] - /' || true
else
  echo "[seed-assets] Volumen ya contiene archivos: $ASSETS_VOLUME_PATH"
fi

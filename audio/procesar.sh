#!/usr/bin/env bash
# Uso: procesar.sh video_entrada.mov video_salida.mp4
# Afina, mezcla y masteriza el audio del vídeo sin recomprimir la imagen.
set -euo pipefail
IN="$1"; OUT="$2"; DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

ffmpeg -hide_banner -loglevel error -i "$IN" -vn -c:a pcm_f32le "$TMP/orig.wav"
python3 -I "$DIR/afinar.py" "$TMP/orig.wav" "$TMP/afinado.wav"
python3 -I "$DIR/reverb_ir.py" "$TMP/ir.wav"

# Limpieza + EQ + compresión, después reverb en paralelo (18 % húmedo)
FX="highpass=f=45,afftdn=nr=8:nf=-50:tn=1,\
equalizer=f=220:t=q:w=1.0:g=-2.5,\
equalizer=f=3200:t=q:w=1.2:g=-2.5,\
equalizer=f=6500:t=q:w=2:g=-1.5,\
highshelf=f=11000:g=1.5,\
acompressor=threshold=-22dB:ratio=2:attack=25:release=300:makeup=2"
ffmpeg -hide_banner -loglevel error -i "$TMP/afinado.wav" -i "$TMP/ir.wav" -filter_complex \
 "[0:a]$FX,asplit[d][w];[w][1:a]afir=dry=10:wet=10[r];[d][r]amix=inputs=2:weights='0.82 0.18':normalize=0[o]" \
 -map "[o]" -c:a pcm_f32le "$TMP/mezcla.wav"

# Normalización de volumen (-14 LUFS, pico real -1 dBTP), dos pasadas
J=$(ffmpeg -hide_banner -i "$TMP/mezcla.wav" -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -I -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -loglevel error -i "$TMP/mezcla.wav" -af \
 "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" \
 -c:a pcm_f32le "$TMP/master.wav"

cp "$TMP/master.wav" "${OUT%.*}_audio.wav"
ffmpeg -hide_banner -loglevel error -y -i "$IN" -i "$TMP/master.wav" -map 0:v:0 -map 1:a:0 \
 -c:v copy -c:a aac -b:a 256k -movflags +faststart "$OUT"

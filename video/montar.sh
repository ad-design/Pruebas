#!/usr/bin/env bash
# Uso: montar.sh video_original.mov audio_masterizado.wav salida.mp4 [inicio_s] [duracion_s]
# Recorta el principio, aplica gradación cálida y superpone los adornos de estilo mexicano.
set -euo pipefail
IN="$1"; AUD="$2"; OUT="$3"; INI="${4:-11.8}"; DUR="${5:-}"
DIR="$(cd "$(dirname "$0")" && pwd)"; CAPAS="${CAPAS:-$(dirname "$OUT")/capas}"
TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
LEN=$(python3 -I -c "print(round(${DUR:-$TOTAL - $INI}, 3))")
FIN=$(python3 -I -c "print(round($LEN - 4.5, 3))")
DURARG=(); [ -n "$DUR" ] && DURARG=(-t "$DUR")

ffmpeg -hide_banner -loglevel error -y \
  -ss "$INI" "${DURARG[@]}" -i "$IN" \
  -ss "$INI" "${DURARG[@]}" -i "$AUD" \
  -stream_loop -1 -framerate 30 -i "$CAPAS/loop/%04d.png" \
  -loop 1 -framerate 30 -i "$CAPAS/titulo.png" \
  -loop 1 -framerate 30 -i "$CAPAS/final.png" \
  -filter_complex "
   [0:v]fps=30,scale=1080:1920,setsar=1,
     eq=saturation=1.18:contrast=1.05:gamma=0.97,
     colorbalance=rs=0.06:gs=-0.01:bs=-0.08:rm=0.07:gm=0.0:bm=-0.06:rh=0.04:bh=-0.05,
     vignette=angle=PI/4.2[base];
   [3:v]format=rgba,fade=t=in:st=0.3:d=0.8:alpha=1,fade=t=out:st=4.2:d=1:alpha=1,trim=0:5.3,setpts=PTS-STARTPTS[tit];
   [4:v]format=rgba,trim=0:4.5,setpts=PTS-STARTPTS,fade=t=in:st=0:d=1:alpha=1,setpts=PTS+$FIN/TB[fin];
   [base][2:v]overlay=0:0:shortest=1[a];
   [a][tit]overlay=0:0:eof_action=pass[b];
   [b][fin]overlay=0:0:eof_action=pass,format=yuv420p[v];
   [1:a]afade=t=in:st=0:d=0.4,afade=t=out:st=$(python3 -I -c "print($LEN-1.2)"):d=1.2[aud]" \
  -map "[v]" -map "[aud]" -t "$LEN" -c:v libx264 -preset medium -crf 19 -profile:v high \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"

# Mejora de audio para vídeos de cuarteto de cuerda

`./procesar.sh entrada.mov salida.mp4` (necesita ffmpeg y `pip install numpy scipy soundfile`)

1. **afinar.py**: corrección polifónica de afinación (phase vocoder por regiones de pico).
   Acerca cada nota a la afinación temperada (La = 440 Hz) al 80 %, como máximo 45 cents.
2. **Limpieza y EQ**: filtro de graves, reducción de ruido suave, −2,5 dB a 220 Hz (resonancia de la sala),
   −2,5 dB a 3,2 kHz (aspereza del arco y del micrófono del móvil), un poco de brillo arriba.
3. **Compresión suave** (2:1) y **reverb de sala** sintética (RT60 1,9 s, 18 %).
4. **Volumen**: −14 LUFS, pico real −1 dBTP. La imagen se copia sin recomprimir.

Parámetros ajustables al principio de `afinar.py` (`STRENGTH`, `MAX_CENTS`) y en `procesar.sh`.

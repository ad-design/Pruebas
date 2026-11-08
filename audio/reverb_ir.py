"""Genera una respuesta al impulso estéreo sintética (sala pequeña y cercana)."""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

sr, rt60, pre = 44100, 1.2, 0.012
n = int(sr * rt60 * 1.2)
t = np.arange(n) / sr
rng = np.random.default_rng(7)
ir = np.zeros((n + int(pre * sr), 2))
for c in range(2):
    noise = rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
    # agudos decaen más rápido (aire); quitar graves turbios
    hf = sosfilt(butter(2, 5000, 'low', fs=sr, output='sos'), noise)
    noise = hf + (noise - hf) * np.exp(-6.91 * t / (rt60 * 0.35))
    noise = sosfilt(butter(2, 180, 'high', fs=sr, output='sos'), noise)
    ir[int(pre * sr):, c] = noise
ir /= np.sqrt((ir ** 2).sum(0)).max()
sf.write(sys.argv[1], ir.astype(np.float32), sr, subtype="FLOAT")

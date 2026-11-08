"""Corrección polifónica de afinación para grabaciones de cuerda.

Método: phase vocoder por regiones de pico (Laroche & Dolson, 1999).
Cada pico espectral entre FMIN y FMAX se lleva hacia la nota temperada más
cercana (A = 440 Hz) con intensidad STRENGTH y como máximo MAX_CENTS.
La región de bins alrededor de cada pico se desplaza en bloque
(desplazamiento entero de bins + rotación de fase acumulada para la parte
fraccionaria), conservando la forma del lóbulo y la fase relativa, lo que
evita el sonido "metálico" de un phase vocoder clásico.
Los armónicos por encima de FMAX no se tocan para preservar el timbre.

Uso: python afinar.py entrada.wav salida.wav
"""
import sys
import numpy as np
import soundfile as sf

N_FFT, HOP = 8192, 1024
FMIN, FMAX = 60.0, 1600.0
STRENGTH = 0.8      # 1.0 = corrección total, 0 = nada
MAX_CENTS = 45.0    # no corrige notas más desafinadas que esto (ambigüedad)
SMOOTH = 0.6        # suavizado temporal (0 = ninguno)
THRESH_DB = -45.0   # picos por debajo de este nivel (rel. al máximo) no se tocan


def frames_of(x):
    pad = np.pad(x, (N_FFT, N_FFT))
    n = 1 + (len(pad) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n)[:, None]
    return pad[idx]


def stft(x, win):
    return np.fft.rfft(frames_of(x) * win, axis=1)


def istft(X, win, length):
    frames = np.fft.irfft(X, n=N_FFT, axis=1) * win
    out = np.zeros(HOP * (len(X) - 1) + N_FFT)
    norm = np.zeros_like(out)
    for i, f in enumerate(frames):
        out[i * HOP:i * HOP + N_FFT] += f
        norm[i * HOP:i * HOP + N_FFT] += win ** 2
    out /= np.maximum(norm, 1e-8)
    return out[N_FFT:N_FFT + length]


def analyse(mag, sr):
    """Devuelve por frame: lista de (inicio, fin, desplazamiento en Hz, bin pico)."""
    lo, hi = int(FMIN * N_FFT / sr), int(FMAX * N_FFT / sr)
    lm = np.log(mag + 1e-12)
    plan, prev = [], {}
    gmax = mag[:, lo:hi].max()
    for t in range(mag.shape[0]):
        m = mag[t]
        thr = max(m[lo:hi].max() * 10 ** (THRESH_DB / 20), gmax * 10 ** (-70 / 20))
        pk = np.where((m[1:-1] > m[:-2]) & (m[1:-1] >= m[2:]))[0] + 1
        pk = pk[(pk >= lo) & (pk < hi) & (m[pk] > thr)]
        regs, cur = [], {}
        if len(pk):
            a, b, c = lm[t, pk - 1], lm[t, pk], lm[t, pk + 1]
            d = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
            f = (pk + d) * sr / N_FFT
            midi = 69 + 12 * np.log2(f / 440.0)
            cents = np.clip((np.round(midi) - midi) * 100, -MAX_CENTS, MAX_CENTS) * STRENGTH
            bounds = np.concatenate(([lo], (pk[:-1] + pk[1:]) // 2 + 1, [hi]))
            for k, p in enumerate(pk):
                # suavizado: hereda el valor del pico más cercano del frame anterior
                near = [q for q in (p - 1, p, p + 1) if q in prev]
                cval = cents[k]
                if near:
                    cval = SMOOTH * prev[near[0]] + (1 - SMOOTH) * cval
                cur[p] = cval
                df = f[k] * (2 ** (cval / 1200) - 1)
                regs.append((bounds[k], bounds[k + 1], df, p))
        plan.append(regs)
        prev = cur
    return plan


def apply(X, plan, sr):
    Y = X.copy()
    nb = X.shape[1]
    rot_prev = {}
    for t, regs in enumerate(plan):
        rot_cur = {}
        for s, e, _, _ in regs:
            Y[t, s:e] = 0
        for s, e, df, p in regs:
            near = [q for q in (p, p - 1, p + 1, p - 2, p + 2) if q in rot_prev]
            rot = (rot_prev[near[0]] if near else 0.0) + 2 * np.pi * df * HOP / sr
            rot = (rot + np.pi) % (2 * np.pi) - np.pi
            rot_cur[p] = rot
            shift = int(round(df * N_FFT / sr))
            ds, de = max(s + shift, 0), min(e + shift, nb)
            Y[t, ds:de] += X[t, ds - shift:de - shift] * np.exp(1j * rot)
        rot_prev = rot_cur
    return Y


if __name__ == "__main__":
    y, sr = sf.read(sys.argv[1], always_2d=True)
    win = np.hanning(N_FFT)
    plan = analyse(np.abs(stft(y.mean(1), win)), sr)  # mismo plan en L y R
    out = np.stack([istft(apply(stft(y[:, c], win), plan, sr), win, len(y))
                    for c in range(y.shape[1])], 1)
    sf.write(sys.argv[2], out.astype(np.float32), sr, subtype="FLOAT")

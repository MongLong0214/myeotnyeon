from functools import lru_cache
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, resample_poly, sosfilt

WORK = Path(__file__).resolve().parent
OUT = WORK.parent
sys.path.insert(0, str(OUT.parent / 'astra_surgery' / 'draft4'))
from edit import DURATION, FPS, cut_time

RATE = 48000
LENGTH = round(DURATION * RATE)
CLOCK = np.arange(LENGTH) / RATE
BUSES = {name: np.zeros((LENGTH, 2), dtype=np.float32) for name in (
    'music', 'operating_room', 'rotary', 'fluids', 'contact_foley', 'fractures',
)}
RECORDINGS = WORK / 'recordings'


def run_ffmpeg(*args):
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-threads', '1', *map(str, args)],
                          capture_output=True, check=True)


def linear(db):
    return 10 ** (db / 20)


@lru_cache
def source(asset):
    media = RECORDINGS / f'{asset}.mp3'
    data = run_ffmpeg('-loglevel', 'error', '-i', media, '-vn', '-ac', '2', '-ar', RATE,
                      '-f', 'f32le', '-').stdout
    return np.frombuffer(data, dtype=np.float32).reshape(-1, 2)


def filtered(data, band):
    if band is None:
        return data.copy()
    low, high = band
    filt = butter(2, (low, high), 'bandpass', fs=RATE, output='sos')
    return sosfilt(filt, data, axis=0).astype(np.float32)


def fade(data, attack, release):
    for seconds, end in [(attack, False), (release, True)]:
        n = min(len(data), round(seconds * RATE))
        if n:
            ramp = np.sin(np.linspace(0, np.pi / 2, n, dtype=np.float32)) ** 2
            if end:
                data[-n:] *= ramp[::-1, None]
            else:
                data[:n] *= ramp[:, None]


def add(bus, time, data):
    start = round(time * RATE)
    assert start >= 0, time
    end = min(start + len(data), LENGTH)
    BUSES[bus][start:end] += data[:end - start]


def edit(asset, start, duration, band, rates):
    x = np.arange(round(duration * RATE), dtype=np.float64) / RATE
    speeds = np.full(len(x), rates) if np.isscalar(rates) else np.interp(x, *zip(*rates))
    cursor = (start + (np.cumsum(speeds) - speeds[0]) / RATE) * RATE
    i = cursor.astype(int)
    frac = (cursor - i).astype(np.float32)[:, None]
    data = source(asset)
    if i[-1] + 1 >= len(data):
        raise ValueError(f'{asset} ends before the selected excerpt at {cursor[-1]/RATE:.3f} s')
    return filtered(data[i] * (1 - frac) + data[i + 1] * frac, band)


def cue(bus, asset, time, start, duration, db, *, band=None, rates=1., pan=0.,
        fade_in=.018, fade_out=.055, rms=False, stereo=False, anchor=None, shape=None,
        channel=None, crest=None, peak_db=None):
    data = edit(asset, start, duration, band, rates)
    if channel is not None:
        data = np.repeat(data[:, channel:channel + 1], 2, axis=1)
    elif not stereo:
        data = np.repeat(data.mean(axis=1, keepdims=True), 2, axis=1)
    fade(data, fade_in, fade_out)
    if shape:
        xt = np.arange(len(data)) / RATE
        data *= linear(np.interp(xt, *zip(*shape)))[:, None]
    if anchor == 'peak':
        time -= np.argmax(np.max(abs(data), axis=1)) / RATE
    elif anchor is not None:
        time -= (anchor - start) / rates
    if crest is not None:
        limit = linear(crest) * np.sqrt(np.mean(data * data))
        data = limit * np.tanh(data / max(limit, 1e-7))
    ref = ((np.sqrt(np.mean(data * data))) if rms else np.max(abs(data)))
    data *= linear(db) / max(ref, 1e-7)
    if peak_db is not None:
        cap = linear(peak_db)
        data = cap * np.tanh(data / cap)
    data *= np.sqrt([1 - pan, 1 + pan]).astype(np.float32)
    add(bus, time, data)


def picture(shot, source_time):
    return round(cut_time(shot, source_time) * FPS) / FPS


# The two musical edits are hidden in the pauses before the crown fractures.
for t, start, dur, db, attack, release in [
    (0.00, 13.20, 1.02, -22.0, .13, .26),
    (1.43, .83, 21.65, -18.1, .49, .22),
    (23.55, 9.55, 29.10, -18.0, .63, 1.95),
]:
    cue('music', 12328, t, start, dur, db, rms=True, stereo=True, band=(60, 13400),
        fade_in=attack, fade_out=release)

music_gain = [
    (0, 0), (3.03, 0), (3.17, -2.8), (3.50, -2.8), (4.11, 0),
    (6.10, 0), (6.25, -3.4), (8.65, -3.4), (9.50, -1.0), (11.90, -1.0),
    (12.43, -4.5), (14.45, -4.5), (16.18, -4.0), (16.52, -7.0), (18.62, -7.0),
    (18.85, -5.1), (21.60, -5.1), (22.05, -1.8), (23.0, -2.0), (24.66, -2.0),
    (25.36, -4.0), (26.56, -1.0), (27.23, -4.0), (28.10, -4.0),
    (28.70, -2.2), (32.20, -3.3), (34.70, -1.3), (36.95, 0),
    (37.35, -5.5), (39.94, -5.5), (40.55, -1.6), (42.5, -.2), (43.15, -3.2),
    (47.78, -3.8), (48.39, -1.0), (49.85, -1.5), (50.24, -4.5), (50.89, -1.0), (52.65, -2.0),
]
BUSES['music'] *= linear(np.interp(CLOCK, *zip(*music_gain)))[:, None]

# Operating room recording, using a clean tone from after the device is switched off.
for t, s, d in [(0., 75.8, 14.4), (13.6, 76.2, 13.8), (26.6, 76.5, 13.8), (39.6, 77.0, 13.05)]:
    cue('operating_room', 406512, t, s, d, -40.5, rms=True, stereo=True, band=(68, 3550),
        fade_in=.76, fade_out=.8)
# Fragments from the actual monitor cadence, rolled off as if across the room.
for t, s, dur, level in [(4.16, 20.46, 1.29, -35.8), (11.14, 22.71, 1.25, -39.4),
                          (35.26, 27.80, 1.30, -36.0), (45.08, 48.53, 1.31, -39.3)]:
    cue('operating_room', 406512, t, s, dur, level, band=(230, 1950),
        stereo=True, fade_in=.11, fade_out=.26)
for a, b, c, d in [(.92, 1.02, 1.20, 1.39), (22.99, 23.09, 23.30, 23.55)]:
    BUSES['operating_room'] *= np.interp(CLOCK, [0, a, b, c, d, DURATION], [1, 1, 0, 0, 1, 1])[:, None]

# Cut-in motion and subtle tissue work. Foley transients follow the contact frames.
for t, s, p, db in [(3.85, 1.39, 1.46, -24), (5.20, 3.41, 3.47, -27),
                    (43.20, 6.00, 6.05, -21), (44.15, 8.47, 8.51, -25)]:
    cue('contact_foley', 456772, t, s, .23, db, band=(185, 5700), pan=-.10, anchor=p)
for t, s, d, db, sp in [(6.36, 3.39, .38, -20, .85), (7.94, 5.74, .37, -18.6, .91), (8.78, 3.49, .29, -24, .95)]:
    cue('contact_foley', 593682, t, s, d, db, band=(185, 6400), rates=sp, pan=-.11, fade_in=.013)
cue('contact_foley', 540338, 7.29, .44, .44, -21.7, band=(185, 6900), rates=.90, pan=-.11,
    fade_in=.022, fade_out=.08)
for t, s, db, sp in [(6.47, 1.64, -27, .84), (8.03, 3.44, -25, .83), (10.12, 5.25, -19, .77),
                      (10.66, 6.63, -22, .76), (11.41, 7.71, -22, .89), (12.00, 2.73, -27, .89),
                      (25.45, 2.20, -19, .89), (28.79, 3.50, -22, .84), (29.73, 5.29, -20, .88),
                      (32.60, 6.38, -20, .80), (33.64, 7.72, -23, .83), (50.24, 1.91, -29, .90)]:
    cue('contact_foley', 211605, t, s, .30, db, band=(135, 5100), rates=sp, pan=.08,
        fade_in=.021, fade_out=.09)

# Real high-speed turbine. Pressed and free-running passages use short speed and level changes.
# The contact layer is a quiet, closely trimmed steel-on-stone recording.
for t, start, d, db, ramps in [
    (12.50, .34, 3.95, -17.7, [(0, 1.035), (.17, .952), (.60, .978), (1.23, .955), (1.70, .979),
                              (2.35, .936), (2.86, .966), (3.55, .949), (3.95, 1.03)]),
    (18.54, 3.88, 3.56, -16.9, [(0, 1.012), (.24, .946), (.66, .986), (1.40, .939), (1.95, .961),
                                 (2.63, .930), (3.00, .967), (3.27, 1.02), (3.56, 1.03)]),
]:
    cue('rotary', 728347, t, start, d, db, rms=True, band=(400, 10100), rates=ramps, pan=.15,
        fade_in=.10, fade_out=.20, crest=10.5, shape=[(0,-4),(.23,0),(d*.53,0),(d*.69,-1.5),(d, -4)])
for t, s, db in [(12.72, 2.12, -24.5), (14.02, 3.45, -25.3), (15.30, 10.20, -25),
                  (18.86, 2.40, -24), (19.91, 10.20, -22.5), (21.01, 13.12, -23)]:
    cue('rotary', 816678, t, s, .61, db, band=(530, 4300), rates=1.10, pan=.12,
        fade_in=.14, fade_out=.14)
cue('rotary', 707344, 27.22, .42, .87, -16.8, rms=True, band=(200, 9900),
    rates=[(0, 1.06),(.16,.98),(.47,.955),(.65,1.02),(.87,1.06)], pan=.12,
    fade_in=.079, fade_out=.12, crest=10.1)
cue('rotary', 816678, 27.34, 2.29, .40, -24, band=(430, 4650), pan=.12,
    fade_in=.10, fade_out=.13)

# Actual dental suction, first in the background and then exposed at the 16.45 s cut.
for t, s, d, db, sp, attack in [(13.41, 3.38, 3.07, -27, .91, .19), (16.34, 3.39, 2.22, -17.7, 1.04, .15),
                                 (38.08, 4.34, 1.91, -25, .93, .30)]:
    cue('fluids', 707321, t, s, d, db, rms=True, band=(125, 6100), rates=sp, pan=-.17,
        fade_in=attack, fade_out=.20, crest=11.8, peak_db=-8.8)
# Bur irrigation and a longer syringe wash. Use the nozzle channel of the contact-mic take.
for t, s, d, db, sp in [(12.66, 4.30, 1.57, -26.9, 1.04), (14.45, 63.62, 1.82, -27.5, .95),
                         (18.66, 22.2, 1.21, -27.6, 1.00), (20.11, 12.92, 1.57, -27.0, .96),
                         (27.30, 9.32, .59, -26.0, 1.02), (37.38, 108.98, 2.92, -20.7, .98)]:
    cue('fluids', 680616, t, s, d, db, rms=True, channel=0, band=(440, 7200), rates=sp,
        pan=-.14, fade_in=.095, fade_out=.17, crest=11.5, peak_db=-15.0)
for t, s, db in [(12.60,.52,-22.5), (15.25,3.07,-25), (18.65,4.20,-22.5),
                  (20.19,5.72,-24.8), (27.29,1.50,-25.5), (37.37,.52,-18.9), (39.05,4.21,-23.4)]:
    cue('fluids', 212178, t, s, .44, db, band=(500, 7800), pan=-.17, fade_in=.032)
for t, s, db in [(5.36, .08, -29), (17.60, .08, -26), (17.98, .28, -27), (35.38, .45, -24),
                  (36.18, .27, -28), (37.91, .06, -24), (39.21, .30, -25), (40.56, .86, -25.2),
                  (41.38, .45, -27.5)]:
    cue('fluids', 209576, t, s, .19, db, band=(165, 5100), rates=.90, pan=.09, fade_in=.016)

# Recorded cellulose fracture. Use different wet celery takes for the hook and the replay.
for t, s, dur, vol, rate in [(1.20, 3.84, .30, -2.35, .91), (23.30, 7.66, .35, -2.60, .96),
                              (28.62, 2.48, .21, -15.7, 1.02), (32.52, 5.63, .24, -16.7, .92)]:
    cue('fractures', 574752, t, s, dur, vol, band=(92, 11400), rates=rate, anchor='peak',
        fade_in=.009, fade_out=.063)
# The same recorded transients provide the lower, short resonant body on the two crown snaps.
for t, s, db in [(1.20, 3.86, -11.0), (23.30, 7.68, -11.8)]:
    cue('fractures', 574752, t + .009, s, .42, db, band=(96, 1250), rates=.70,
        anchor='peak', pan=.07, fade_in=.013, fade_out=.094)

# The scrape that loads the elevator and quieter scrapes during the separate releases.
for t, s, dur, db, speed in [(.39, .24, .33, -24, .78), (22.68, .26, .40, -20.0, .71),
                              (25.30, .24, .51, -19, .80), (28.40, .28, .31, -20.2, 1.0),
                              (32.20, .23, .37, -19.6, .95)]:
    cue('contact_foley', 816680, t, s, dur, db, band=(240, 5200), rates=speed, pan=-.12,
        fade_in=.027, fade_out=.10)
# Real tweezers on a tooth, and the softer mechanical clicks of the holder.
for t, s, pk, db in [(24.75, 5.57, 5.65, -23), (42.75, 2.89, 2.95, -25),
                     (44.83, 8.03, 8.11, -24.5), (48.95, 6.57, 6.65, -17.9), (50.25, 5.72, 5.78, -23.0)]:
    cue('contact_foley', 155913, t, s, .25, db, band=(280, 9100), pan=.11, anchor=pk)
# Needle/linen friction and thread pull in sync with emergence, first tension and final draw.
for ts, s, pk, d, db, sp in [(38.43, 9.30, 9.37, .29, -22.0, .84), (39.16, 47.80, 47.89, .37, -23.5, .94),
                              (39.75, 23.34, 23.46, .41, -17.4, .83), (40.17, 17.24, 17.36, .40, -20.4, .83)]:
    cue('contact_foley', 563779, picture('closure', ts), s, d, db, band=(200, 7600),
        rates=sp, pan=.06, anchor=pk, fade_in=.025, fade_out=.10)
cue('contact_foley', 10219, picture('closure', 41.32), 2.04, .41, -16.6, band=(310, 10500),
    pan=.12, anchor='peak', fade_in=.015, fade_out=.09)
# A single subdued instrument set-down, with close cloth/specimen and tray in perspective.
cue('contact_foley', 481935, 50.43, 12.37, .42, -23.5, band=(225, 6800), pan=.19,
    anchor=12.45, fade_in=.012, fade_out=.19)


def measure(path):
    details = run_ffmpeg('-i', path, '-vn', '-af', 'loudnorm=print_format=json', '-f', 'null', '-').stderr.decode()
    return json.JSONDecoder().raw_decode(details[details.rindex('{'):])[0]


def peak_factors(program):
    # Five ms look-ahead with a short release, shared across every print so the stems sum.
    high_rate = resample_poly(program, 4, 1, axis=0)
    peak = np.max(np.abs(high_rate).reshape(LENGTH, 4, 2), axis=(1, 2))
    del high_rate
    return maximum_filter1d(peak, size=2 * round(.009 * RATE) + 1)


def master():
    program = np.sum(list(BUSES.values()), axis=0)
    wav_path = WORK / 'master.wav'
    mux_path = WORK / 'surgery_draft5_realsfx.mp4'
    sf.write(wav_path, program, RATE, subtype='FLOAT')
    first = measure(wav_path)
    gain = -14.0 - float(first['input_i'])
    print('Premix', first, flush=True)
    peak = peak_factors(program)
    ceiling = -2.3
    for attempt in range(6):
        # Keep codec headroom. The limiter acts on the loudest short transients.
        f = np.minimum(1., linear(ceiling) / np.maximum(1e-7, peak * linear(gain)))
        f = uniform_filter1d(f, size=2 * round(.004 * RATE) + 1) * linear(gain)
        sf.write(wav_path, program * f[:,None], RATE, subtype='PCM_24')
        run_ffmpeg('-v', 'error', '-y', '-i', OUT.parent/'astra_surgery_draft5.mp4', '-i', wav_path,
                   '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
                   '-ar', RATE, '-movflags', '+faststart', mux_path)
        measured = measure(mux_path)
        print(f'Pass {attempt + 1} gain {gain:+.2f} dB', measured, flush=True)
        error = -14.0 - float(measured['input_i'])
        if abs(error) <= .08 and float(measured['input_tp']) <= -1.5:
            break
        gain += error
        if float(measured['input_tp']) > -1.5:
            ceiling -= float(measured['input_tp']) + 1.9
    else:
        raise RuntimeError('AAC did not reach the requested loudness and true peak')
    if mux_path.stat().st_size >= 25_000_000:
        raise ValueError('MP4 exceeds 25 MB')
    for bus, data in BUSES.items():
        sf.write(OUT / 'stems' / f'{bus}.wav', data * f[:,None], RATE, subtype='PCM_24')
    mux_path.replace(OUT / mux_path.name)


if __name__ == '__main__':
    master()

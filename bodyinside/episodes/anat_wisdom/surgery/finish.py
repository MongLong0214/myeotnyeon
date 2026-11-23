"""Mix the draft audio, encode the portrait MP4, and make its nine-step sheet."""
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BEATS = json.loads((HERE / "timing.json").read_text())
FPS = 20
SIZE = (540, 960)
LENGTH = BEATS[-1]["end"]
SHEET_LABELS = ("신경관 옆 드릴", "국소 마취", "절개와 잇몸 박리", "뼈 제거", "치아 분할",
                "머리와 뿌리 제거", "빈 발치와와 세척", "봉합", "혈병 형성")


def noise(length, lo, hi, sample_rate, rng):
    band = butter(2, (lo, hi), btype="bandpass", fs=sample_rate, output="sos")
    wet = sosfilt(band, rng.standard_normal(length))
    return wet / max(np.std(wet), .001)


def audio():
    rate, samples = wavfile.read(HERE/"audio/narration.wav")
    voice = samples.astype(np.float32) / 32768
    rng = np.random.default_rng(34)
    fx = np.zeros_like(voice, dtype=np.float64)
    room = noise(len(fx), 110, 960, rate, rng)*.0014
    fx += room

    for first, last, with_drill in [
        (0,2.96,True), (13.49,18.20,True), (19.05,22.95,True),
        (27.21,27.87,True), (33.87,36.29,False)]:
        lo, hi = round(first*rate), round(last*rate)
        t = np.arange(hi-lo)/rate
        tail = (hi-lo)/rate - t
        attack = np.clip((t+.02)/.145,.03,1)
        decay = np.clip(tail/.23,0,1)
        jet = .0095*noise(len(t),1250,6400,rate,rng)*(1+.26*np.sin(18*t)+.14*np.sin(48*t))
        if with_drill:
            phase = 2*np.pi*1900*t + .19*np.sin(31.5*t) + 2.2*np.sin(6.5*t)
            jet += (.015*np.sin(phase)+.004*np.sin(2.03*phase)+.008*noise(len(t),470,3100,rate,rng))
        fx[lo:hi] += jet*attack*decay

    for time, strength in [(7.5,.005),(9.16,.004),(23.87,.055),(24.02,.03),
                           (25.71,.013),(27.77,.015),(28.8,.017),(31.0,.016),(39.56,.005)]:
        lo = round(time*rate)
        n = round(.13*rate)
        t = np.arange(n)/rate
        live = np.minimum(t/.007,1)*np.exp(-t/.036)
        contact = noise(n,285,4400,rate,rng) + .48*np.sin(2*np.pi*278*t)
        fx[lo:lo+n] += strength*live*contact

    wavfile.write(HERE/"audio/mix.wav", rate, np.clip(voice+fx,-1,1).astype(np.float32))
    return HERE/"audio/mix.wav"


def contact_sheet():
    pad, gap, width, height, label_h = 28, 16, 315, 560, 52
    page = Image.new("RGB", (2*pad+3*width+2*gap, 2*pad+3*(height+label_h)+2*gap), "#171313")
    paint = ImageDraw.Draw(page)
    font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 24)
    time_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 16)
    for i, (beat, label) in enumerate(zip(BEATS, SHEET_LABELS)):
        f = HERE/"frames"/f"f_{round(beat['sample']*FPS)+1:04d}.png"
        x, y = pad+(i%3)*(width+gap), pad+(i//3)*(height+label_h+gap)
        with Image.open(f) as im:
            page.paste(im.resize((width,height),Image.Resampling.LANCZOS), (x,y))
        paint.text((x,y+height+14), label, font=font, fill="#f5e8e2")
        second = int(beat["sample"])
        paint.text((x+width,y+height+19),f"{second//60:02d}:{second%60:02d}",
                   font=time_font,fill="#c9b5ac",anchor="rt")
    page.save(OUT/"sheet_surgery1.png")


def main():
    frames = sorted((HERE/"frames").glob("f_*.png"))
    expected = [f"f_{n:04d}.png" for n in range(1,FPS*LENGTH+1)]
    if [frame.name for frame in frames] != expected:
        raise SystemExit(f"Expected {len(expected)} sequential draft frames, found {len(frames)}.")
    with Image.open(frames[-1]) as image:
        if image.size != SIZE:
            raise SystemExit(f"Wrong draft resolution: {image.size}")
    audio_path = audio()
    encoded = HERE/"encoded.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-start_number","1",
                    "-i",str(HERE/"frames/f_%04d.png"),"-i",str(audio_path),
                    "-map","0:v:0","-map","1:a:0","-c:v","libx264","-crf","18","-preset","fast",
                    "-vf","setsar=1,format=yuv420p","-c:a","aac","-b:a","160k",
                    "-movflags","+faststart","-t",str(LENGTH),str(encoded)],check=True)
    contact_sheet()
    encoded.replace(OUT/"surgery_draft1.mp4")


if __name__ == "__main__":
    main()

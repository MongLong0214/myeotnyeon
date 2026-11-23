"""Shot boundaries and source-time landmarks in seconds on the draft 3 procedure clock."""
FPS = 20
# One optical setup per shot. Landmarks between cuts control local playback speed.
SHOTS = [
    ("fracture", [(0,23.52),(1.20,23.88),(3.20,24.58)]),
    ("anaesthesia", [(3.20,3.78),(4.05,4.35),(5.15,5.77),(6.15,6.59)]),
    ("access", [(6.15,7.22),(9.40,9.64),(12.50,12.80)]),
    ("osteotomy", [(12.50,13.47),(16.45,16.46)]),
    ("aspiration", [(16.45,16.46),(18.55,18.06)]),
    ("section", [(18.55,19.20),(21.90,22.86),(24.70,24.89)]),
    ("delivery", [(24.70,24.89),(26.95,26.59),(28.25,28.32),(30.85,29.91),(31.80,30.38),(34.95,32.84)]),
    ("socket", [(34.95,32.84),(37.35,33.91),(40.30,36.17),(42.40,37.28)]),
    ("closure", [(42.40,37.59),(44.75,39.32),(46.60,40.48),(48.65,42.04)]),
    ("specimen", [(48.65,44.10),(52.65,48.10)]),
]
DURATION = SHOTS[-1][1][-1][0]
FRAMES = round(DURATION * FPS)

def at(t):
    for shot, marks in SHOTS:
        if t < marks[-1][0]:
            for (a,x),(b,y) in zip(marks,marks[1:]):
                if t < b:
                    return shot,x+(y-x)*(t-a)/(b-a)
    return SHOTS[-1][0], SHOTS[-1][1][-1][1]

def cut_time(shot, source):
    marks=dict(SHOTS)[shot]
    for (a,x),(b,y) in zip(marks,marks[1:]):
        if x <= source <= y:
            return a+(b-a)*(source-x)/(y-x)
    raise ValueError((shot,source))

import glob, time
from imgutils.detect import detect_person, detect_heads
from imgutils.detect.hand import detect_hands
fs = sorted(glob.glob("/private/tmp/claude-501/-Users-isaac-projects-myeotnyeon/58cac5c6-fe3f-4c22-a6f4-20e085a7b119/scratchpad/fr/*.png"))
t=time.time()
for f in fs:
    h = detect_hands(f); p = detect_person(f); hd = detect_heads(f)
    print(f.split('/')[-1], "person",len(p),"heads",len(hd),"hands",len(h), [round(s,2) for _,_,s in h])
print("sec/frame", round((time.time()-t)/len(fs),2))

import time
from rapidocr import RapidOCR, LangRec, OCRVersion, ModelType
eng = RapidOCR(params={"Rec.lang_type": LangRec.KOREAN, "Rec.ocr_version": OCRVersion.PPOCRV5, "Rec.model_type": ModelType.MOBILE})
for n in ["016","008","012","014"]:
    t=time.time(); r = eng("/private/tmp/claude-501/-Users-isaac-projects-myeotnyeon/58cac5c6-fe3f-4c22-a6f4-20e085a7b119/scratchpad/fr/f_%s.png"%n)
    print(n, round(time.time()-t,2), [(tx, round(float(s),2), [int(v) for v in b[0]]+[int(v) for v in b[2]]) for tx,s,b in zip(r.txts or [], r.scores or [], r.boxes if r.boxes is not None else [])])

from analyze import *
# Normalized accepted-boundary strips, distinct from the rejected-candidate archive.
cs=list(csv.DictReader((R/'cuts.csv').open()));cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'))
for start in range(0,len(cs),12):
 g=cs[start:start+12];sh=Image.new('RGB',(1200,len(g)*116));dr=ImageDraw.Draw(sh)
 for j,c in enumerate(g):
  y=j*116;fr=int(c['frame']);dr.text((3,y),f"Cut{int(c['cut_id']):03} f{fr} {float(c['time_s']):.3f}s {c['transition_type']}",font=ImageFont.truetype(FONT,12),fill='white')
  for off in range(-3,3):sh.paste(imageframe(cap,fr+off,(200,90)),((off+3)*200,y+22))
 sh.save(R/'ref'/f'final_boundaries_{start//12+1:02}.jpg',quality=91)
cap.release()

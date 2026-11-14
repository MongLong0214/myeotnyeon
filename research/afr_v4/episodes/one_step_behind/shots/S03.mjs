import {held,beat,stepPose} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps),d=p.delay??.55;const s=stepPose(a,.7,2.3,-.45,.45),r=stepPose(a,.7+d,2.3+d,.52,1.42);w.frame({time:a,heroX:s.x,readerX:r.x,step:s,readerStep:r,look:.5*beat(a,3.1,3.8),smile:.3});}

export function soundEvents(p={}){const d=p.delay??0.55;return [{t:1.5,type:'step',pan:-.25},{t:2.3,type:'step',pan:-.25},{t:1.5+d,type:'step',pan:.25},{t:2.3+d,type:'step',pan:.25}];}

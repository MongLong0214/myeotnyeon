import {held,beat,stepPose} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps),d=p.delay??.6;const s=stepPose(a,.8,2.5,.45,-.6),r=stepPose(a,.8+d,2.5+d,1.42,.37);w.frame({time:a,heroX:s.x,readerX:r.x,step:s,readerStep:r,look:.5,smile:.2,lean:-.025*beat(a,3.5,4)});}

export function soundEvents(p={}){const d=p.delay??0.6;return [{t:1.65,type:'step',pan:-.25},{t:2.5,type:'step',pan:-.25},{t:1.65+d,type:'step',pan:.25},{t:2.5+d,type:'step',pan:.25}];}

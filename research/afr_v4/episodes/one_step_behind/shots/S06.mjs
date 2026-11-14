import {held,beat} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps);w.frame({time:a,heroX:-.6,readerX:.37,look:.45*(1-beat(a,1,2)),nod:.1*Math.sin(beat(a,1,2)*Math.PI),smile:.4+beat(a,.5,2),wide:.25*beat(t,0,6)});}

export function soundEvents(){return [{t:1.7,type:'bell',hz:659.255,gain:.07}];}

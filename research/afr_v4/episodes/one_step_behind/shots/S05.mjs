import {held,beat} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps);w.frame({time:a,heroX:-.6,readerX:.37,look:.45,reveal:beat(t,0,1.3),smile:.5});}

export function soundEvents(){return [{t:2.2,type:'bell',hz:523.251,gain:.07}];}

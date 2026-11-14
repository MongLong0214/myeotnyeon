import {held,beat} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps);w.frame({time:a,look:.53*beat(a,.6,1.5)*(1-beat(a,4.6,5.8)),smile:.3,lean:.025*beat(a,.8,1.8)});}

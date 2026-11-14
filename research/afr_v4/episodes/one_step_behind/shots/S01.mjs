import {held,beat} from '../../../src/motion.mjs';
export function pose(w,t,p,fps){const a=held(t,fps);w.frame({time:a,wide:1-beat(t,0,6)*.35});}

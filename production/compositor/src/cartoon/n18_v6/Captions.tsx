import React from 'react';
import type {Caption} from '@remotion/captions';
export const Captions=({cue}:{cue:(Caption&{start:number;end:number})|undefined})=>cue?<div style={{position:'absolute',left:75,right:75,bottom:36,textAlign:'center',fontSize:55,lineHeight:1.2,fontWeight:800,color:'#fff4da'}}>{cue.text}</div>:null;

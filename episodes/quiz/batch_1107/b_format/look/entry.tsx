import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {BStandard} from '../BStandard';
import {Q021LookFilm} from './ShotsQ021';
import {Q024LookFilm} from './ShotsQ024';
import {FILMS_V1,FILMS_V2} from './v2/Shots2';
const L1:React.FC<{c:any}>=({c})=><BStandard c={c} look={{film:FILMS_V1[c.qid]}}/>;
const L2:React.FC<{c:any}>=({c})=><BStandard c={c} look={{film:FILMS_V2[c.qid]}}/>;
// Look-dev compositions: BEFORE = the current template, LOOK = the same case with the look layer switched on.
export const LOOK_FILMS:Record<string,any>={q021:Q021LookFilm,q024:Q024LookFilm};
const Look:React.FC<{c:any}>=({c})=><BStandard c={c} look={{film:LOOK_FILMS[c.qid]}}/>;
registerRoot(()=><>
 <Composition id="BEFORE" component={BStandard as any} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props}:any)=>({durationInFrames:props.c.n})}/>
 <Composition id="LOOK" component={Look} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props}:any)=>({durationInFrames:props.c.n})}/>
 <Composition id="LOOK1" component={L1} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props}:any)=>({durationInFrames:props.c.n})}/>
 <Composition id="LOOK2" component={L2} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props}:any)=>({durationInFrames:props.c.n})}/>
</>);

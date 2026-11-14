import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Shot} from './Shot';
import {Lineup} from './Lineup';
registerRoot(()=> <>
 <Composition id="SHOT" component={Shot} width={1080} height={1920} fps={30} durationInFrames={210}/>
 <Composition id="LINEUP" component={Lineup} width={1080} height={1920} fps={30} durationInFrames={60}/>
</>);

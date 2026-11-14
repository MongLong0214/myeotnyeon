import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Test,Parts} from './Art';
registerRoot(()=> <>
 <Composition id="TEST" component={Test} width={1080} height={1920} fps={30} durationInFrames={90}/>
 <Composition id="PARTS" component={Parts} width={1080} height={1080} fps={30} durationInFrames={1} defaultProps={{kind:'polar' as const}}/>
</>);

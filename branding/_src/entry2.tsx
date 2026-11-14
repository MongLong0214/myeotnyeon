import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Pfp2,Banner2,Wm2,Compare2} from './Cheol2';
registerRoot(()=><>{(['A','B','C'] as const).map(d=><React.Fragment key={d}>
 <Composition id={`pfp-${d}`} component={Pfp2 as any} width={800} height={800} fps={30} durationInFrames={1} defaultProps={{d}}/>
 <Composition id={`wm-${d}`} component={Wm2 as any} width={150} height={150} fps={30} durationInFrames={1} defaultProps={{d}}/>
 <Composition id={`banner-${d}`} component={Banner2 as any} width={2560} height={1440} fps={30} durationInFrames={1} defaultProps={{d}}/>
</React.Fragment>)}
 <Composition id="compare" component={Compare2} width={2370} height={1640} fps={30} durationInFrames={1}/></>);

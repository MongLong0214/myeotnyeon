import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Standard} from './Standard';
registerRoot(()=> <><Composition id="VIDEO" component={Standard} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as any}} calculateMetadata={({props})=>({durationInFrames:props.c.n})}/><Composition id="COVER" component={Standard} width={1080} height={1920} fps={30} durationInFrames={1} defaultProps={{c:{} as any,cover:true}}/></>);

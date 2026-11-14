import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {BStandard} from './BStandard';
registerRoot(()=> <><Composition id="VIDEO" component={BStandard} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props})=>({durationInFrames:props.c.n})}/><Composition id="COVER" component={BStandard} width={1080} height={1920} fps={30} durationInFrames={1} defaultProps={{c:{} as never,cover:true}}/></>);

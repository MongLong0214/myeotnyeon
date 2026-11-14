import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {ModelSheet} from './Sheet';
import {Film} from './Film';
registerRoot(()=> <>
 <Composition id="SHEET" component={ModelSheet} width={1080} height={1920} fps={30} durationInFrames={60} defaultProps={{kind:'polar' as never}}/>
 <Composition id="VIDEO" component={Film} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{c:{} as never}} calculateMetadata={({props})=>({durationInFrames:(props.c as {n:number}).n})}/>
 <Composition id="COVER" component={Film} width={1080} height={1920} fps={30} durationInFrames={1} defaultProps={{c:{} as never,cover:true}}/>
</>);

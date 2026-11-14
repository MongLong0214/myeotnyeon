import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {V3} from './V3';
import data from './render.json';
registerRoot(()=> <Composition id="VIDEO" component={V3} width={1080} height={1920} fps={30} durationInFrames={data.durationInFrames}/>);

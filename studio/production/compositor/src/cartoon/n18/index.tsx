import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Episode} from './Episode';
import data from './data.json';
registerRoot(()=> <Composition id="N18CartoonV4" component={Episode} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);

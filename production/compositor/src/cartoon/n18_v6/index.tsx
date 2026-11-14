import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Episode} from './Episode';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data.json';
registerRoot(()=> <Composition id="N18CartoonV6" component={Episode} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);

import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {EpisodeV6Fix2} from './EpisodeV6Fix2';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data_v6fix2.json';
registerRoot(()=> <Composition id="N18CartoonV6Fix2" component={EpisodeV6Fix2} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);

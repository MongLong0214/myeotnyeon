import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {EpisodeV6Fix} from './EpisodeV6Fix';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data_v6fix.json';
registerRoot(()=> <Composition id="N18CartoonV6Fix" component={EpisodeV6Fix} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);

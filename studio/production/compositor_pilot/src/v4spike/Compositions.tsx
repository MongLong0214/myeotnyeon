import React from 'react';
import { Composition } from 'remotion';
import { PathA } from './PathA';
import { PathB } from './PathB';
import { SpikeProps } from './scene';

export const V4SpikeCompositions: React.FC = () => <>
  {([['V4SPIKE-A', PathA], ['V4SPIKE-B', PathB]] as const).map(([id, component]) =>
    <Composition key={id} id={id} component={component} width={1080} height={1920} fps={30} durationInFrames={90}
      defaultProps={{landscape:false} satisfies SpikeProps}
      calculateMetadata={({props})=>({width:props.landscape?1920:1080,height:props.landscape?1080:1920})}/>
  )}
</>;

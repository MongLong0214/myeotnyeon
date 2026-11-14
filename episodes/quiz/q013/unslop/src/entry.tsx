import React from 'react';
import {Composition,Still,registerRoot} from 'remotion';
import {Unslop,CoverUnslop} from './Unslop';
import data from './render.json';
registerRoot(()=> <><Composition id="VIDEO" component={Unslop} width={1080} height={1920} fps={30} durationInFrames={data.durationInFrames}/><Still id="COVER" component={CoverUnslop} width={1080} height={1920}/></>);

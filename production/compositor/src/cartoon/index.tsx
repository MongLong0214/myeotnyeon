import React from 'react';
import {Composition,Still,registerRoot} from 'remotion';
import {Pilot} from './Pilot';
import {StyleSheet} from './StyleSheet';
const Root:React.FC=()=><><Composition id="CartoonPilot45" component={Pilot} width={1920} height={1080} fps={30} durationInFrames={1350}/><Still id="CartoonStyleSheet" component={StyleSheet} width={3600} height={3360}/></>;
registerRoot(Root);

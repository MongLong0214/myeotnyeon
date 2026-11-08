import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Quiz} from '../src/Quiz';
const Root = () => <Composition id="EndBoundary" component={Quiz} width={1080} height={1920} fps={30} durationInFrames={1200} defaultProps={{doc: null as any}} />;
registerRoot(Root);

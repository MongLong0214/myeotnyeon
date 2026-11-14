import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {PFP,WM,Banner,Board} from './Brand';
import {Pfp2,Wm2,Banner2} from './Cheol2';
const PFPK=()=><Pfp2 d="C"/>,WMK=()=><Wm2 d="C"/>,BannerK=()=><Banner2 d="C"/>;
const C=[['gts','guessthesentence'],['nnd','nannenderu'],['bcl','beastclashtoon']] as const;
registerRoot(()=><>{C.map(([ch,h])=><React.Fragment key={ch}>
 <Composition id={`pfp-${ch}`} component={PFP as any} width={800} height={800} fps={30} durationInFrames={1} defaultProps={{ch}}/>
 <Composition id={`wm-${ch}`} component={WM as any} width={150} height={150} fps={30} durationInFrames={1} defaultProps={{ch}}/>
 <Composition id={`banner-${ch}`} component={Banner as any} width={2560} height={1440} fps={30} durationInFrames={1} defaultProps={{ch}}/>
 <Composition id={`board-${ch}`} component={Board as any} width={2240} height={1800} fps={30} durationInFrames={1} defaultProps={{ch,handle:h}}/>
</React.Fragment>)}
 <Composition id="pfp-chk" component={PFPK} width={800} height={800} fps={30} durationInFrames={1}/>
 <Composition id="wm-chk" component={WMK} width={150} height={150} fps={30} durationInFrames={1}/>
 <Composition id="banner-chk" component={BannerK} width={2560} height={1440} fps={30} durationInFrames={1}/>
 <Composition id="board-chk" component={Board as any} width={2240} height={1800} fps={30} durationInFrames={1} defaultProps={{ch:'chk',handle:'cheolkeong'}}/>
</>);

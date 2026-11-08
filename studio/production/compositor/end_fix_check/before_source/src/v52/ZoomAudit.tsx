import React, {useLayoutEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';

export const ZoomAudit: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    const hero = document.querySelector('[data-v52-zoom]') as HTMLElement | null;
    if (hero) {
      const report = {frame, scale: Number(hero.dataset.v52Zoom), transform: getComputedStyle(hero).transform};
      const h = delayRender(`HOOKCHECK52SCALE ${JSON.stringify(report)} END`);continueRender(h);
    }
  }, [frame]);
  return <>{children}</>;
};

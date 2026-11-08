import React, {useLayoutEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';
import type {QuizDoc} from './Quiz';
// Runs only in the opt-in audit composition; existing SafeAudit checks every glyph.
export const HookAudit: React.FC<{doc: QuizDoc; children: React.ReactNode}> = ({doc, children}) => {
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    const h = delayRender('v5 loaded-font audit');
    document.fonts.ready.then(() => {
      const head = document.querySelector('[data-v5-headline]') as HTMLElement | null;
      const cta = document.querySelector('[data-v5-cta]') as HTMLElement | null;
      const text = document.body.innerText;
      const report = {frame, headline: head?.innerText ?? '', headlineSize: head ? parseFloat(getComputedStyle(head).fontSize) : 0,
        hookVisible: !!head && head.getBoundingClientRect().height > 0, branding: text.includes('형량 퀴즈'),
        cta: !!cta && text.includes('다음 판결도 맞혀보세요') && text.includes('구독'),
        caption: doc.subtitles.find(s => frame >= s.from_ && frame < s.to)?.text ?? ''};
      const r = delayRender(`HOOKCHECK ${JSON.stringify(report)} END`);continueRender(r);continueRender(h);
    });
  }, [frame, doc]);
  return <>{children}</>;
};

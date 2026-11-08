import React, {useLayoutEffect} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';
import type {QuizDoc} from './Quiz';

export const HookAudit51: React.FC<{doc: QuizDoc; children: React.ReactNode}> = ({doc, children}) => {
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    const h = delayRender('v51 loaded-font metrics');
    document.fonts.ready.then(() => {
      const head = document.querySelector('[data-v51-headline]') as HTMLElement | null;
      const rows = Array.from(document.querySelectorAll<HTMLElement>('[data-v51-headline-row]'));
      const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d')!;
      const heights = rows.flatMap(row => {
        const heights: number[] = []; const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const cs = getComputedStyle(node.parentElement!);ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
          heights.push(...[...(node.textContent ?? '')].filter(c => /[가-힣0-9]/.test(c)).map(c => {const m = ctx.measureText(c);return m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;}));
        }
        return heights;
      });
      const card = document.querySelector('[data-v51-cta-card]')?.getBoundingClientRect();
      const root = document.querySelector('[data-v51-cta]')?.getBoundingClientRect();
      const report = {frame, headline: head?.innerText ?? '', headlineSize: head ? parseFloat(getComputedStyle(head).fontSize) : 0, minGlyphHeight: heights.length ? Math.min(...heights) : 0,
        hookVisible: !!head && head.getBoundingClientRect().height > 0, branding: document.body.innerText.includes('형량 퀴즈'),
        cta: !!card && document.body.innerText.includes('다음 판결도') && document.body.innerText.includes('맞혀보세요') && document.body.innerText.includes('구독'),
        ctaAreaRatio: card && root ? card.width * card.height / (root.width * root.height) : 0,
        caption: doc.subtitles.find(s => frame >= s.from_ && frame < s.to)?.text ?? ''};
      const r = delayRender(`HOOKCHECK51 ${JSON.stringify(report)} END`);continueRender(r);continueRender(h);
    });
  }, [frame, doc]);
  return <>{children}</>;
};

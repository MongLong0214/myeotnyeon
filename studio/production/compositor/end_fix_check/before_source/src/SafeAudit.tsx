// Mobile safe-area audit (owner 2026-10-26: "모바일에서 하나도 안 짤리는지 극도로 타이트하게").
// Wraps a 1080×1920 composition, measures every visible text glyph box on every frame and logs any box
// that enters a zone a phone can hide, or that is clipped by an overflow:hidden parent.
// Zones (video px): side crop when the app fills taller phones (x < 110, x > 970), status bar / Dynamic
// Island / app top icons (y < 190), title + channel block (y > 1540), action rail (x > 880 and y > 900).
import React, { useLayoutEffect, useRef } from 'react';
import { continueRender, delayRender, useCurrentFrame } from 'remotion';

export const ZONES = { left: 110, right: 970, top: 190, bottom: 1540, railX: 880, railY: 900 };
const TOL = 1;

const visible = (el: Element | null): boolean => {
  for (let e = el; e && e instanceof HTMLElement; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
  }
  return true;
};

export const SafeAudit: React.FC<{ children: React.ReactNode; label: string }> = ({ children, label }) => {
  const f = useCurrentFrame();
  const root = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const h = delayRender(`audit ${f}`);
    const el = root.current;
    if (el) {
      const rr = el.getBoundingClientRect();
      const k = rr.width / 1080;
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const out: string[] = [];
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        const txt = (n.textContent ?? '').replace(/\s+/g, ' ').trim();
        if (!txt || !visible(n.parentElement)) continue;
        const range = document.createRange(); range.selectNodeContents(n);
        for (const r of Array.from(range.getClientRects())) {
          if (r.width < 1 || r.height < 1) continue;
          const x0 = (r.left - rr.left) / k, y0 = (r.top - rr.top) / k, x1 = (r.right - rr.left) / k, y1 = (r.bottom - rr.top) / k;
          const why: string[] = [];
          if (x0 < ZONES.left - TOL) why.push('side-L'); if (x1 > ZONES.right + TOL) why.push('side-R');
          if (y0 < ZONES.top - TOL) why.push('top'); if (y1 > ZONES.bottom + TOL) why.push('bottom');
          if (x1 > ZONES.railX + TOL && y1 > ZONES.railY + TOL) why.push('rail');
          // clipped by an overflow:hidden ancestor (text cut at a panel edge)
          for (let p = n.parentElement; p && p !== el; p = p.parentElement) {
            if (getComputedStyle(p).overflow === 'hidden') {
              const pr = p.getBoundingClientRect();
              if (r.left < pr.left - TOL || r.right > pr.right + TOL || r.top < pr.top - TOL || r.bottom > pr.bottom + TOL) why.push('clipped');
              break;
            }
          }
          if (why.length) out.push(`${why.join('+')} "${txt.slice(0, 24)}" ${Math.round(x0)},${Math.round(y0)}-${Math.round(x1)},${Math.round(y1)}`);
        }
      }
      // Remotion does not forward console output, but it prints delayRender labels — carry the result in one.
      const report = delayRender(`AUDIT ${label} f=${f} n=${out.length}${out.length ? ' | ' + out.join(' | ').replace(/["\n]/g, "'") : ''} END`);
      continueRender(report);
    }
    continueRender(h);
  }, [f, label]);
  return <div ref={root} style={{ position: 'relative', width: 1080, height: 1920, overflow: 'hidden' }}>{children}</div>;
};

import { continueRender, delayRender, staticFile } from 'remotion';

const faces: [string, string, string][] = [
  ['Pretendard', 'fonts/Pretendard-Regular.woff2', '400'],
  ['Pretendard', 'fonts/Pretendard-Medium.woff2', '500'],
  ['Pretendard', 'fonts/Pretendard-SemiBold.woff2', '600'],
  ['Pretendard', 'fonts/Pretendard-Bold.woff2', '700'],
  ['Pretendard', 'fonts/Pretendard-ExtraBold.woff2', '800'],
  ['Noto Serif KR', 'fonts/NotoSerifKR.ttf', '200 900'],
  ['Black Han Sans', 'fonts/BlackHanSans-Regular.ttf', '400'],
];
let started = false;
export const loadFonts = () => {
  if (started || typeof document === 'undefined') return;
  started = true;
  const h = delayRender('fonts');
  Promise.all(
    faces.map(([fam, src, w]) => {
      const f = new FontFace(fam, `url(${staticFile(src)})`, { weight: w });
      return f.load().then((ff) => (document as any).fonts.add(ff));
    }),
  ).then(() => continueRender(h), (e) => { console.error(e); continueRender(h); });
};

// House palette from the v1.0 bible (Navy/Paper/Ink/Teal/Amber). Colour encodes
// information type, never a person's guilt.
export const C = {
  navy: '#172B3A',
  paper: '#F3F1E9',
  ink: '#253746',
  teal: '#177D87',
  tealBright: '#3FB6C0',
  amber: '#C68A35',
  amberBright: '#E6B061',
  grey: '#8A9399',
  dim: 'rgba(8,14,20,0.72)',
  glass: 'rgba(10,18,26,0.78)',
  line: 'rgba(243,241,233,0.22)',
};
// epistemic labels (bible §08)
export const TAGS: Record<string, { label: string; color: string; dashed?: boolean }> = {
  recon: { label: '기록 기반 재구성', color: C.paper },
  concept: { label: '개념도 · 실제 배치 아님', color: C.grey, dashed: true },
  party: { label: '당사자 주장', color: C.amberBright, dashed: true },
  defense: { label: '피고인·변호인 주장', color: C.amberBright, dashed: true },
  prosecution: { label: '공소사실·검찰 주장', color: C.amberBright, dashed: true },
  court: { label: '법원 판단', color: C.tealBright },
  courtSummary: { label: '법원 판단 · 보도 기반 요약', color: C.tealBright },
  analysis: { label: '제작진 해설', color: '#B9C4CA' },
  material: { label: '자료 요약', color: C.paper },
  unknown: { label: '보도로 확인되지 않음', color: C.grey, dashed: true },
  law: { label: '법조문', color: C.paper },
  report: { label: '보도 내용', color: C.paper },
  reaction: { label: '온라인 반응 · 요약', color: C.grey, dashed: true },
};
export const FONT = "'Pretendard', 'Apple SD Gothic Neo', sans-serif";
export const DISPLAY = "'Black Han Sans', 'Pretendard', sans-serif";
export const SERIF = "'Noto Serif KR', serif";

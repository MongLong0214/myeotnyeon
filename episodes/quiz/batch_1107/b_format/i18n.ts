import React from 'react';
// Locale layer for the B3 format (case.json "locale": "ko" default | "en" | "ja"). Every fixed on-screen string of the
// template lives here; case-specific text (hook, choices, opinion, pops, prop cards) comes from the spec in its language.
// Fonts: the template's two families ('Do Hyeon' display, 'Quiet Sans' body) are re-pointed per locale, so no component
// needs to change its fontFamily. en: Noto Sans (OFL), ja: Noto Sans JP (OFL), both variable 100-900, bundled locally.
export type Locale='ko'|'en'|'ja';
export const localeOf=(c:unknown):Locale=>((c as {locale?:Locale})?.locale)??'ko';
export const FONTS:Record<Locale,[family:string,file:string,weight:string][]>={
 ko:[['Do Hyeon','DoHyeon-Regular.ttf','400'],['Quiet Sans','Pretendard-ExtraBold.woff2','800']],
 en:[['Do Hyeon','NotoSans-VF.ttf','100 900'],['Quiet Sans','NotoSans-VF.ttf','100 900']],
 ja:[['Do Hyeon','NotoSansJP-VF.ttf','100 900'],['Quiet Sans','NotoSansJP-VF.ttf','100 900']],
};
type S={answer:(letter:string,label:string)=>string;subscribe:string;year:(y:string)=>string;month:(m:string)=>string;yearLabel:string;nth:(k:number)=>string;prosecutor:string;hours:(h:number)=>string;capW:number};
export const STR:Record<Locale,S>={
 ko:{answer:(l,lb)=>`정답 ${l} · ${lb}`,subscribe:'구독',year:y=>`${y}년`,month:m=>`${m}월`,yearLabel:'연도',nth:k=>`${k}번`,prosecutor:'구형',hours:h=>`${h}시간`,capW:1},
 en:{answer:(l,lb)=>`Answer ${l} · ${lb}`,subscribe:'SUBSCRIBE',year:y=>y,month:m=>['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][Number(m)-1]??m,yearLabel:'YEAR',nth:k=>`#${k}`,prosecutor:'Prosecutors ask',hours:h=>`${h} hrs`,capW:.56},
 ja:{answer:(l,lb)=>`正解 ${l} · ${lb}`,subscribe:'登録',year:y=>`${y}年`,month:m=>`${m}月`,yearLabel:'西暦',nth:k=>`${k}回`,prosecutor:'求刑',hours:h=>`${h}時間`,capW:1},
};
export const str=(c:unknown)=>STR[localeOf(c)];
export const LocaleCtx=React.createContext<Locale>('ko');
export const useStr=()=>STR[React.useContext(LocaleCtx)];
// width of a line in em (Latin ~0.56, caps/digits ~0.66, CJK 1)
export const em=(L:Locale,line:string)=>[...line].reduce((a,ch)=>a+(/[\u3000-\u9fff\uff00-\uffef\uac00-\ud7af]/.test(ch)?1:L==='en'?(/[A-Z0-9$]/.test(ch)?.66:.54):.56),0);
// caption size: 72px unless the longest line would overflow the 1000px caption box (Latin glyphs ~0.56em, CJK 1em)
export const captionSize=(c:unknown,text:string)=>{const L=localeOf(c);if(L==='ko')return 72;
 const w=Math.max(...text.split('\n').map(l=>em(L,l)));
 return Math.max(44,Math.min(72,Math.floor(860/Math.max(1,w))));};

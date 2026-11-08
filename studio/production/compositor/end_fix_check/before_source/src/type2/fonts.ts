import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';
const faces: [string,string,string][] = [
 ['T2 Myeongjo','NanumMyeongjo-Regular.ttf','400'],['T2 Myeongjo','NanumMyeongjo-Bold.ttf','700'],['T2 Myeongjo','NanumMyeongjo-ExtraBold.ttf','800'],
 ['T2 Song','SongMyung-Regular.ttf','400'],['T2 Coding','NanumGothicCoding-Regular.ttf','400'],['T2 Coding','NanumGothicCoding-Bold.ttf','700'],
 ['T2 Head','DoHyeon-Regular.ttf','400'],['T2 Black','BlackHanSans-Regular.ttf','400'],['T2 Sans','Pretendard-SemiBold.woff2','600'],['T2 Sans','Pretendard-Bold.woff2','700'],
];
let started=false;
export const loadType2Fonts=()=>{
 if(started||typeof document==='undefined')return;started=true;const handle=delayRender('type2 local OFL fonts');
 Promise.all(faces.map(async([family,file,weight])=>{const face=await new FontFace(family,`url(${staticFile(`fonts/${file}`)})`,{weight}).load();document.fonts.add(face);})).then(()=>continueRender(handle),cancelRender);
};

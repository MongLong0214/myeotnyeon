// v2 lip sync: Korean syllables placed on the narration's real voiced runs (per-frame loudness from lipdata.py),
// then the Rhubarb timing rules: every shape holds >= 2 frames, lips close 1 frame before ㅁ/ㅂ/ㅃ/ㅍ, final ㅁ/ㅂ/ㅍ
// close at the end of a long syllable, pauses < 4 frames keep the last shape, and the track leads the audio by 1 frame.
// Each frame also carries an openness (0..1) from the loudness, so loud syllables open wider.
import {jamo,type Viseme} from '../../../../../../production/lf_toon/src/lipsync';
import q021 from './lipdata/q021.json';
import q024 from './lipdata/q024.json';
import q033 from './lipdata/q033.json';
import q034 from './lipdata/q034.json';
import q035 from './lipdata/q035.json';
import q036 from './lipdata/q036.json';
import q037 from './lipdata/q037.json';
import q038 from './lipdata/q038.json';
import q039 from './lipdata/q039.json';
import q040 from './lipdata/q040.json';
import q041 from './lipdata/q041.json';
import q042 from './lipdata/q042.json';
import q043 from './lipdata/q043.json';
import q044 from './lipdata/q044.json';
import q045 from './lipdata/q045.json';
import q046 from './lipdata/q046.json';
import q047 from './lipdata/q047.json';
import q048 from './lipdata/q048.json';
export const LIPDATA:Record<string,{rms:number[]}>={q021,q024,q033,q034,q035,q036,q037,q038,q039,q040,q041,q042,q043,q044,q045,q046,q047,q048};
export type Track2={from:number;v:Viseme[];open:number[]};
const MED:Viseme[]=['AI','E','AI','E','E','E','E','E','O','AI','E','E','O','U','E','E','E','U','EU','E','E'];
const LIPS0=new Set([6,7,8,17]),LIPS1=new Set([16,17,26]);
// en/ja (no Hangul): Latin vowel groups or katakana morae (spec "lip" = reading) as jamo-like {initial,medial,final}:
// medial a0 i20 u13 e4 o8; initial 6 (closed lips) for m/b/p and マ/バ/パ rows.
const KV='アイウエオ',KROW:Record<string,string>={};
['アイウエオ','カキクケコ','ガギグゲゴ','サシスセソ','ザジズゼゾ','タチツテト','ダヂヅデド','ナニヌネノ','ハヒフヘホ','バビブベボ','パピプペポ','マミムメモ','ヤ_ユ_ヨ','ラリルレロ','ワ___ヲ'].forEach(r=>[...r].forEach((ch,k)=>{if(ch!=='_')KROW[ch]=KV[k]+(/[バビブベボパピプペポマミムメモ]/.test(ch)?'m':'');}));
const MV:Record<string,number>={a:0,i:20,u:13,e:4,o:8,y:20,'ア':0,'イ':20,'ウ':13,'エ':4,'オ':8};
const pseudoJamo=(text:string)=>{const out:{initial:number;medial:number;final:number}[]=[];
 const kata=text.replace(/[\u3041-\u3096]/g,ch=>String.fromCharCode(ch.charCodeAt(0)+0x60));
 if(/[\u30a0-\u30ff]/.test(kata)){for(const ch of kata){const r=KROW[ch];if(r)out.push({initial:r.endsWith('m')?6:0,medial:MV[r[0]],final:0});
   else if(ch==='ン')out.push({initial:0,medial:18,final:0});else if(ch==='ー'&&out.length)out.push({...out[out.length-1],initial:0});}return out;}
 for(const m of text.toLowerCase().matchAll(/([^aeiouy\s\W]*)([aeiouy]+)/g))out.push({initial:/[mbp]$/.test(m[1])?6:0,medial:MV[m[2][0]]??0,final:0});
 return out;};
export const talkTrack2=(text:string,on:number,off:number,rms?:number[]):Track2=>{
 const ko=[...text].filter(ch=>jamo(ch)).map(ch=>jamo(ch)!),syl=ko.length?ko:pseudoJamo(text);
 const from=on-2,n=off-on+5,v:Viseme[]=Array(n).fill('rest'),open:number[]=Array(n).fill(0);
 const e=(i:number)=>rms?(rms[from+1+i]??0):(i>=2&&i<n-3?.7:0);
 // voiced runs (gaps < 3 frames merged)
 const runs:[number,number][]=[];let i=0;
 while(i<n){while(i<n&&e(i)<.28)i++;if(i>=n)break;let j=i;while(j<n&&(e(j)>=.28||(j+1<n&&e(j+1)>=.28)||(j+2<n&&e(j+2)>=.28)))j++;runs.push([i,j]);i=j;}
 if(!runs.length)runs.push([2,n-3]);
 // syllables to runs by length (largest remainder), each run >= 1 syllable when possible
 const tot=runs.reduce((a,[s,t])=>a+t-s,0),share=runs.map(([s,t])=>syl.length*(t-s)/tot),cnt=share.map(Math.floor);
 let left=syl.length-cnt.reduce((a,b)=>a+b,0);share.map((x,k)=>[x-Math.floor(x),k]).sort((a,b)=>b[0]-a[0]).forEach(([,k])=>{if(left>0){cnt[k]++;left--;}});
 let si=0;
 runs.forEach(([s,t],k)=>{const ss=syl.slice(si,si+cnt[k]);si+=cnt[k];if(!ss.length)return;
  // a syllable with a final consonant is held ~35% longer
  const w=ss.map(j=>1+(j.final?.35:0)),W=w.reduce((a,b)=>a+b,0);let cur=s;
  ss.forEach((j,q)=>{const a=Math.round(cur),b=Math.round(cur+(t-s)*w[q]/W);cur+=(t-s)*w[q]/W;
   for(let x=a;x<b&&x<n;x++)v[x]=MED[j.medial];
   if(LIPS1.has(j.final)&&b-a>=4){v[b-1]='MBP';v[b-2]='MBP';}
   if(LIPS0.has(j.initial))for(const x of [a-1,a])if(x>=0&&x<n)v[x]='MBP';});
 });
 for(let x=1;x<n;x++)if(v[x]==='rest'){let y=x;while(y<n&&v[y]==='rest')y++;if(y<n&&y-x<4)for(let z=x;z<y;z++)v[z]=v[x-1];x=y;}
 for(let x=1;x<n-1;x++)if(v[x]!==v[x-1]&&v[x]!==v[x+1])v[x]=v[x-1];
 for(let x=0;x<n;x++)open[x]=v[x]==='rest'||v[x]==='MBP'?0:Math.min(1,.35+.8*e(x+1));
 return {from,v,open};
};
export const lipAt=(tr:Track2|undefined,f:number)=>{if(!tr)return {v:'rest' as Viseme,open:0};const i=f-tr.from;return {v:tr.v[i]??'rest',open:tr.open[i]??0};};

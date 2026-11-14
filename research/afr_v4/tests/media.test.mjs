import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';import os from 'node:os';import zlib from 'node:zlib';
import {crc32} from '../src/core.mjs';
import {encodeFrames,verifyVideo} from '../tools/runtime.mjs';
function png(w,h,value){function chunk(name,data){const n=Buffer.from(name),o=Buffer.alloc(data.length+12);o.writeUInt32BE(data.length);n.copy(o,4);data.copy(o,8);o.writeUInt32BE(crc32(Buffer.concat([n,data])),data.length+8);return o;}const ih=Buffer.alloc(13);ih.writeUInt32BE(w);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=6;const raw=Buffer.alloc((w*4+1)*h,0);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const k=y*(w*4+1)+1+x*4;raw[k]=value;raw[k+1]=90;raw[k+2]=120;raw[k+3]=255;}return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}
test('real FFmpeg encode/decode fixture; missing required sound is rejected',async()=>{
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'af-media-'));try{
  fs.mkdirSync(path.join(tmp,'shot/frames'),{recursive:true});for(let i=0;i<4;i++)fs.writeFileSync(path.join(tmp,`shot/frames/f_${String(i).padStart(6,'0')}.png`),png(160,90,80+i*10));
  const spec={width:160,height:90,fps:24,frames:4};const file=await encodeFrames(tmp,'shot',spec);
  await verifyVideo(file,spec);await assert.rejects(()=>verifyVideo(file,{...spec,audio:true}),/audio missing/);
 }finally{fs.rmSync(tmp,{recursive:true,force:true});}
});

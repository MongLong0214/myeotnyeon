import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

export const sha = data => crypto.createHash('sha256').update(data).digest('hex');
export const gitBlob = data => crypto.createHash('sha1').update(`blob ${data.length}\0`).update(data).digest('hex');
export const stable = x => JSON.stringify(normalize(x));
function normalize(x) {
  if (Array.isArray(x)) return x.map(normalize);
  if (x && typeof x === 'object') return Object.fromEntries(Object.keys(x).sort().map(k=>[k,normalize(x[k])]));
  return x;
}
export function assert(condition, message) { if (!condition) throw new Error(message); }
export function inside(root, target) {
  const r = path.relative(path.resolve(root), path.resolve(target));
  return r === '' || (!r.startsWith('..'+path.sep) && r !== '..' && !path.isAbsolute(r));
}
export function rejectLinks(target) {
  let p = path.resolve(target);
  while (true) {
    if (fs.existsSync(p) || (()=>{try{fs.lstatSync(p);return true;}catch{return false;}})()) {
      const s = fs.lstatSync(p);
      assert(!s.isSymbolicLink(), `Refusing symbolic-link output path: ${p}`);
      if (s.isFile()) assert(s.nlink === 1, `Refusing multiply-linked output: ${p}`);
    }
    const q=path.dirname(p); if(q===p) break; p=q;
  }
}
export function safeOutput(root, relative) {
  const p=path.resolve(root,relative); assert(inside(root,p), 'Output escapes output root');
  rejectLinks(p); return p;
}
export function atomicWrite(root, relative, data) {
  const p=safeOutput(root,relative); fs.mkdirSync(path.dirname(p),{recursive:true});
  const tmp=`${p}.${process.pid}.${crypto.randomBytes(6).toString('hex')}.tmp`;
  try { fs.writeFileSync(tmp,data,{flag:'wx'}); rejectLinks(p); fs.renameSync(tmp,p); }
  finally { if(fs.existsSync(tmp)) fs.unlinkSync(tmp); }
  return p;
}
export function validateEpisode(e) {
  assert(typeof e.id==='string' && /^[A-Za-z0-9_-]+$/.test(e.id),'Invalid episode id');
  assert(Number.isInteger(e.fps)&&e.fps>=12&&e.fps<=60,'Integer fps 12..60 required');
  assert(Array.isArray(e.shots)&&e.shots.length>0,'At least one shot required');
  assert(e.contentRole==='original','Reference content cannot be delivered as original content');
  let at=0; const ids=new Set();
  const timeline=e.shots.map(s=>{
    assert(/^[A-Za-z0-9_-]+$/.test(s.id)&&!ids.has(s.id),'Duplicate/invalid shot id'); ids.add(s.id);
    assert(Number.isInteger(s.frames)&&s.frames>0,`Invalid frame count: ${s.id}`);
    assert(typeof s.module==='string'&&s.module.endsWith('.mjs'),`Executable shot module missing: ${s.id}`);
    assert(Array.isArray(s.dependencies)&&s.dependencies.includes(s.module),`Declare shot module dependency: ${s.id}`);
    assert(s.states?.start && s.states?.end,`Continuity states missing: ${s.id}`);
    const result={...s,startFrame:at,endFrame:at+s.frames}; at+=s.frames; return result;
  });
  for(let i=1;i<timeline.length;i++){
    const a=timeline[i-1].states.end,b=timeline[i].states.start;
    for(const k of Object.keys(b)) if(k in a) assert(stable(a[k])===stable(b[k]),`Continuity mismatch ${timeline[i].id}: ${k}`);
  }
  return {shots:timeline,frames:at,seconds:at/e.fps};
}
export function visualKey(e,s,profile,files,device={}) {
  // Deliberately excludes title, review questions, voice, music, and unrelated shots.
  return sha(stable({version:4,episode:e.id,fps:e.fps,aspect:e.aspect,seed:e.seed,
    look:e.lookSettings||{},shot:{id:s.id,frames:s.frames,module:s.module,params:s.params||{},states:s.states},profile,files,device}));
}
const table=Array.from({length:256},(_,n)=>{for(let j=0;j<8;j++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
export function crc32(buf){let c=0xffffffff;for(const b of buf)c=table[(c^b)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
export function checkPNG(buf,w,h){
  assert(Buffer.isBuffer(buf)&&buf.length>32,'Truncated PNG');
  assert(buf.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])),'Not PNG');
  let at=8,header=null,end=false;const idats=[];
  while(at+12<=buf.length){const len=buf.readUInt32BE(at),type=buf.toString('ascii',at+4,at+8);
    assert(len<256*1024*1024 && at+12+len<=buf.length,'Truncated PNG chunk');
    const data=buf.subarray(at+8,at+8+len);
    assert(crc32(buf.subarray(at+4,at+8+len))===buf.readUInt32BE(at+8+len),'PNG CRC mismatch');
    if(type==='IHDR')header=data;
    if(type==='IDAT')idats.push(data);
    if(type==='IEND'){end=true;at+=12+len;break;}
    at+=12+len;
  }
  assert(header&&end&&idats.length,'Incomplete PNG');
  assert(header.readUInt32BE(0)===w&&header.readUInt32BE(4)===h,'PNG dimensions mismatch');
  assert(header[8]===8&&[2,6].includes(header[9])&&header[12]===0,'Expected noninterlaced 8-bit RGB/RGBA PNG');
  const channels=header[9]===6?4:3;
  const data=zlib.inflateSync(Buffer.concat(idats),{maxOutputLength:(w*channels+1)*h+16});
  assert(data.length===(w*channels+1)*h,'PNG pixel data length mismatch');
  return true;
}
export function fileHashes(root,relativePaths){
  const list=[...new Set(relativePaths)].sort();
  return Object.fromEntries(list.map(p=>{
    const f=path.resolve(root,p);assert(inside(root,f),`Dependency escapes project: ${p}`);
    assert(fs.existsSync(f)&&fs.statSync(f).isFile(),`Missing dependency: ${p}`);
    return [p,sha(fs.readFileSync(f))];
  }));
}
export function assertUnchanged(root,hashes){
  for(const [p,h] of Object.entries(hashes))assert(fs.existsSync(path.resolve(root,p))&&sha(fs.readFileSync(path.resolve(root,p)))===h,`Source changed during render: ${p}`);
}

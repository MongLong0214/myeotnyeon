import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {assert,sha,stable,gitBlob,validateEpisode,visualKey,fileHashes,assertUnchanged,atomicWrite,checkPNG,safeOutput,rejectLinks} from '../src/core.mjs';
import {server,openBrowser,lockOutput,command,probe,verifyVideo,encodeFrames,getChrome} from './runtime.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const OUT=path.join(ROOT,'out');
const argv=process.argv.slice(2),mode=argv.shift()||'help';
function opt(k,def){const i=argv.indexOf('--'+k);return i<0?def:argv[i+1];}
const has=k=>argv.includes('--'+k),profile=opt('profile','review');
const PRESETS={review:{width:360,height:640},detail:{width:540,height:960},final:{width:1080,height:1920}};
const episodeRel=opt('episode','episodes/one_step_behind/episode.json');
const aborted=new AbortController();
for(const sig of ['SIGINT','SIGTERM'])process.once(sig,()=>aborted.abort(new Error(sig)));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function list(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?list(path.join(dir,x.name)):[path.join(dir,x.name)]);}
function referenceSources(){
 const lock=read(path.join(ROOT,'reference.lock.json'));
 for(const [f,h] of Object.entries(lock.gitBlobs)){
  const p=path.join(ROOT,'vendor/todai',f);assert(fs.existsSync(p),'Pinned source is missing. Run npm run setup; no fallback preview is permitted.');
  assert(gitBlob(fs.readFileSync(p))===h,`Pinned reference modified: ${f}. Do not silently swap to another renderer.`);
 }
 return lock;
}
function load(){
 const p=path.resolve(ROOT,episodeRel);assert(p.startsWith(path.join(ROOT,'episodes')+path.sep),'Episode outside episodes/');
 const e=read(p),timeline=validateEpisode(e);assert(PRESETS[profile],'Unknown profile');return {e,timeline};
}
function deps(e,s){
 const upstream=[...list(path.join(ROOT,'vendor/todai/vendor/three')),path.join(ROOT,'vendor/todai/src/anime.js')].filter(p=>/\.(js|mjs)$/.test(p)).map(p=>path.relative(ROOT,p));
 return fileHashes(ROOT,[...e.commonDependencies,...s.dependencies,...upstream]);
}
async function mediaPrereq(){
 await command(process.env.FFPROBE||'ffprobe',['-version']);
 const r=await command(process.env.FFMPEG||'ffmpeg',['-hide_banner','-encoders']);assert(r.stdout.includes('libx264'),'FFmpeg libx264 encoder required');
}
async function reference(){
 const lock=referenceSources();await mediaPrereq();rejectLinks(OUT);fs.mkdirSync(OUT,{recursive:true});
 const release=lockOutput(OUT,'reference/.lock'),http=await server(ROOT);let browser;
 try{
  browser=await openBrowser({allowSoftware:has('allow-software')});const page=await browser.newPage({viewport:{width:1920,height:1080}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto(http.url+'/vendor/todai/index.html?render=1');await page.evaluate(()=>window.ready);
  const info=await page.evaluate(()=>window.__info());assert(has('allow-software')||!/(swiftshader|llvmpipe|software)/i.test(info.renderer),'Software renderer detected. Pass --allow-software only for an explicit slow diagnostic.');
  for(const t of lock.benchmark.stillsSeconds){const url=await page.evaluate(t=>window.renderFrame(t,{fmt:'png'}),t);const b=Buffer.from(url.split(',')[1],'base64');checkPNG(b,1920,1080);atomicWrite(OUT,`reference/still_${t}.png`,b);}
  if(!has('stills-only')){
   const dir='reference/motion';for(let f=0;f<lock.benchmark.motionFrames;f++){
    if(aborted.signal.aborted)throw aborted.signal.reason;
    const t=(lock.benchmark.motionStartFrame+f)/24;
    const url=await page.evaluate(t=>window.renderFrame(t,{fmt:'png'}),t),b=Buffer.from(url.split(',')[1],'base64');checkPNG(b,1920,1080);
    atomicWrite(OUT,`${dir}/frames/f_${String(f).padStart(6,'0')}.png`,b);
   }
   await encodeFrames(OUT,dir,{width:1920,height:1080,fps:24,frames:72},aborted.signal);
  }
  assert(errors.length===0,errors.join('\n'));referenceSources();
  atomicWrite(OUT,'reference/RESULT.json',JSON.stringify({role:'THIRD-PARTY REPRODUCTION, NOT OUR WORK',repository:lock.repository,commit:lock.commit,info,at:new Date().toISOString(),comparisonWithAuthorFrames:'Not automatically scored. Compare source docs/stills visually.'},null,2));
  console.log('Reference-source reproduction written to out/reference. This is not an original episode.');
 }finally{await browser?.close();await http.close();release();}
}
async function render(){
 referenceSources();await mediaPrereq();const {e,timeline}=load(),selected=opt('shot',null);
 const shots=selected?timeline.shots.filter(s=>s.id===selected):timeline.shots;assert(shots.length,'Unknown selected shot');
 rejectLinks(OUT);fs.mkdirSync(OUT,{recursive:true});const release=lockOutput(OUT,`${e.id}/${profile}/.lock`),http=await server(ROOT);let browser;
 try{
  browser=await openBrowser({allowSoftware:has('allow-software')});
  for(const s of shots){
   const hashes=deps(e,s),page=await browser.newPage({viewport:PRESETS[profile]});const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   try{
    const q=new URLSearchParams({episode:episodeRel,shot:s.id,...Object.fromEntries(Object.entries(PRESETS[profile]).map(([k,v])=>[k,String(v)])),capture:'1'});
    await page.goto(http.url+'/web/index.html?'+q);await page.evaluate(()=>window.ready);
    const info=await page.evaluate(()=>window.factoryInfo);
    assert(has('allow-software')||!/(swiftshader|llvmpipe|software)/i.test(info.gpu),'Software rendering detected; do not interpret its speed as your GPU speed.');
    const key=visualKey(e,s,PRESETS[profile],hashes,{gpu:info.gpu,browser:browser.version()});
    const dir=`${e.id}/${profile}/${s.id}/${key}`;const statePath=safeOutput(OUT,`${dir}/frames.json`);
    const state=fs.existsSync(statePath)?read(statePath):{key,frames:{}};assert(state.key===key,'Cache job mismatch');
    let rendered=0,reused=0;const start=performance.now();
    // Test the renderer actually seeks deterministically within this runtime before caching.
    const f=Math.min(7,s.frames-1),a=await page.evaluate(f=>window.renderFrame(f),f);
    await page.evaluate(()=>window.renderFrame(0));const b=await page.evaluate(f=>window.renderFrame(f),f);
    assert(a===b,'Stateful render detected. Absolute frame seeking must be fixed, not hidden with retries.');
    for(let frame=0;frame<s.frames;frame++){
     if(aborted.signal.aborted)throw aborted.signal.reason;
     const rel=`${dir}/frames/f_${String(frame).padStart(6,'0')}.png`,target=safeOutput(OUT,rel);
     let valid=false;
     if(fs.existsSync(target)&&state.frames[frame]){try{const old=fs.readFileSync(target);checkPNG(old,info.width,info.height);valid=sha(old)===state.frames[frame];}catch{}}
     if(valid){reused++;continue;}
     const url=await page.evaluate(f=>window.renderFrame(f),frame),data=Buffer.from(url.split(',')[1],'base64');checkPNG(data,info.width,info.height);
     assert(errors.length===0,errors.join('\n'));atomicWrite(OUT,rel,data);state.frames[frame]=sha(data);atomicWrite(OUT,`${dir}/frames.json`,JSON.stringify(state));rendered++;
    }
    assertUnchanged(ROOT,hashes);assert(errors.length===0,errors.join('\n'));
    const picture=safeOutput(OUT,`${dir}/picture.mp4`),meta=safeOutput(OUT,`${dir}/result.json`);
    let result=fs.existsSync(meta)?read(meta):null;
    const encoderKey=sha(stable({worker:sha(fs.readFileSync(path.join(ROOT,'tools/runtime.mjs'))),ffmpeg:(await command(process.env.FFMPEG||'ffmpeg',['-version'])).stdout.split('\n')[0],fps:e.fps,profile:PRESETS[profile]}));
    if(!result||result.encoderKey!==encoderKey||!fs.existsSync(picture)||sha(fs.readFileSync(picture))!==result.pictureHash){
     await encodeFrames(OUT,dir,{...PRESETS[profile],fps:e.fps,frames:s.frames},aborted.signal);assertUnchanged(ROOT,hashes);
    }
    result={key,encoderKey,shot:s.id,role:'original-unreviewed',profile,frames:s.frames,...PRESETS[profile],fps:e.fps,picture:path.relative(OUT,picture).split(path.sep).join('/'),pictureHash:sha(fs.readFileSync(picture)),hashes,device:info,browser:browser.version(),rendered,reused,elapsedSeconds:(performance.now()-start)/1000};
    atomicWrite(OUT,`${dir}/result.json`,JSON.stringify(result,null,2));atomicWrite(OUT,`${e.id}/${profile}/${s.id}/current.json`,JSON.stringify(result,null,2));
    console.log(`${s.id}: ${rendered} rendered / ${reused} reused — ${result.elapsedSeconds.toFixed(2)}s`);
   }finally{await page.close();}
  }
 }finally{await browser?.close();await http.close();release();}
}
async function assemble(){
 const {e,timeline}=load();await mediaPrereq();rejectLinks(OUT);fs.mkdirSync(OUT,{recursive:true});const release=lockOutput(OUT,`${e.id}/${profile}/.lock`);
 try{
  const shotResults=timeline.shots.map(s=>{
   const f=safeOutput(OUT,`${e.id}/${profile}/${s.id}/current.json`);assert(fs.existsSync(f),`Missing actual ${profile} render: ${s.id}`);const r=read(f);
   assert(r.role==='original-unreviewed'&&r.profile===profile&&r.frames===s.frames,'Wrong shot kind/profile/length');
   assert(stable(r.hashes)===stable(deps(e,s)),'Shot sources changed; render this shot first');
   const expected=visualKey(e,s,PRESETS[profile],r.hashes,{gpu:r.device.gpu,browser:r.browser});assert(expected===r.key,'Episode/shot settings changed; rerender affected shot');
   const p=safeOutput(OUT,r.picture);assert(sha(fs.readFileSync(p))===r.pictureHash,'Shot file replaced or corrupted');return r;
  });
  const stems=[],voiceDir=`${e.id}/audio`;
  for(const line of e.audio?.lines||[]){
   const p=safeOutput(OUT,`${voiceDir}/${line.id}.wav`);
   if(!fs.existsSync(p)){assert(profile!=='final',`Final narration missing: ${line.id}. Run tools/voice.py or provide licensed WAV with matching manifest.`);continue;}
   const meta=read(safeOutput(OUT,`${voiceDir}/${line.id}.json`));
   assert(meta.text===line.text&&meta.voice===e.audio.voice,'Voice text/settings changed');assert(meta.wavHash===sha(fs.readFileSync(p)),'Voice file changed');
   const pr=await probe(p),dur=Number(pr.format.duration);assert(dur<=line.maxFrames/e.fps+.03,'Narration exceeds slot. Fix editorial timing, do not silently speed it up.');
   stems.push({path:p,at:audioAt(line,timeline)/e.fps,gain:1,hash:meta.wavHash});
  }
  const sfx=safeOutput(OUT,`${voiceDir}/effects.wav`);if(fs.existsSync(sfx)){
   const sm=read(safeOutput(OUT,`${voiceDir}/effects.json`));
   const sourceDependencies=Object.fromEntries(timeline.shots.map(s=>[s.module,sha(fs.readFileSync(path.join(ROOT,s.module)))]));
   const timing=timeline.shots.map(({id,frames,module,params})=>({id,frames,module,params}));
   const expected=sha(stable({fps:e.fps,timing,sourceDependencies,worker:sha(fs.readFileSync(path.join(ROOT,'tools/sound.mjs')))}));
   assert(sm.timingKey===expected&&sm.sha256===sha(fs.readFileSync(sfx)),'Effect timing/source changed: run npm run sound. Existing 3D frames will not be rerendered.');
   stems.push({path:sfx,at:0,gain:.55,hash:sm.sha256});
  }
  if(profile==='final')assert(stems.length>0||e.audio?.intentionalSilence===true,'Final sound missing');
  const key=sha(stable({editor:sha(fs.readFileSync(fileURLToPath(import.meta.url))),mediaWorker:sha(fs.readFileSync(path.join(ROOT,'tools/runtime.mjs'))),pictures:shotResults.map(x=>x.pictureHash),stems:stems.map(({hash,at,gain})=>({hash,at,gain})),fps:e.fps,frames:timeline.frames,profile}));
  const dir=`${e.id}/${profile}/edit/${key}`,target=safeOutput(OUT,`${dir}/${profile}.mp4`),manifest=safeOutput(OUT,`${dir}/result.json`);
  let cached=false;if(fs.existsSync(manifest)&&fs.existsSync(target)){const m=read(manifest);cached=sha(fs.readFileSync(target))===m.outputHash&&m.audioCount===stems.length;}
  if(!cached){
   const concat=shotResults.map(r=>`file '${safeOutput(OUT,r.picture).replaceAll('\\','/').replaceAll("'","'\\''")}'`).join('\n');
   atomicWrite(OUT,`${dir}/shots.txt`,concat+'\n');
   const temp=safeOutput(OUT,`${dir}/assembled.${process.pid}.tmp.mp4`);
   const args=['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',safeOutput(OUT,`${dir}/shots.txt`)];
   for(const x of stems)args.push('-i',x.path);
   if(stems.length){const filters=stems.map((s,i)=>`[${i+1}:a]aresample=48000,asetpts=PTS-STARTPTS,volume=${s.gain},adelay=${Math.round(s.at*1000)}:all=1[a${i}]`);filters.push(stems.map((_,i)=>`[a${i}]`).join('')+`amix=inputs=${stems.length}:normalize=0,apad,atrim=duration=${timeline.seconds},alimiter=limit=0.89:level=0:latency=1[mix]`);
    args.push('-filter_complex',filters.join(';'),'-map','0:v:0','-map','[mix]','-c:a','aac','-b:a','192k','-ar','48000','-ac','2');
   }else args.push('-map','0:v:0','-an');
   args.push('-c:v','copy','-t',String(timeline.seconds),'-movflags','+faststart',temp);
   try{
    await command(process.env.FFMPEG||'ffmpeg',args,{signal:aborted.signal});
    await verifyVideo(temp,{...PRESETS[profile],fps:e.fps,frames:timeline.frames,audio:stems.length>0});
    // Do not publish an edit if sources changed while mixing.
    shotResults.forEach(r=>assertUnchanged(ROOT,r.hashes));for(const s of stems)assert(sha(fs.readFileSync(s.path))===s.hash,'Audio changed during mix');
    rejectLinks(target);fs.renameSync(temp,target);
    atomicWrite(OUT,`${dir}/result.json`,JSON.stringify({key,outputHash:sha(fs.readFileSync(target)),audioCount:stems.length,frames:timeline.frames,profile},null,2));
   }finally{if(fs.existsSync(temp))fs.unlinkSync(temp);}
  }
  // Notes are not part of render/encode keys.
  atomicWrite(OUT,`${dir}/review.md`,`# ${e.title}\n\n${profile==='final'?'Final-size candidate. Creative sign-off is not inferred from successful encoding.':'Actual 3D review; this is not a storyboard slide show.'}\n\n${stems.length?'Audio tracks included: '+stems.length:'NO VOICE OR MUSIC: motion/look inspection only.'}\n\n${e.reviewQuestions.join('\n')}\n\nTimecoded notes only; no scores or per-shot signature required.\n`);
  const srt=(e.audio?.lines||[]).map((x,i)=>`${i+1}\n${stamp(audioAt(x,timeline)/e.fps)} --> ${stamp((audioAt(x,timeline)+x.maxFrames)/e.fps)}\n${x.text}\n`).join('\n');
  atomicWrite(OUT,`${dir}/captions.srt`,srt);atomicWrite(OUT,`${e.id}/${profile}/LATEST.txt`,path.relative(OUT,target)+'\n');
  console.log(`${cached?'REUSED':'ASSEMBLED'} ${target}`);
 }finally{release();}
}
function audioAt(line,timeline){if(!line.shot)return line.atFrame;const s=timeline.shots.find(x=>x.id===line.shot);assert(s,'Unknown audio anchor shot');const f=s.startFrame+line.localFrame;assert(Number.isInteger(f)&&f>=0&&f+line.maxFrames<=timeline.frames,'Audio anchor/range outside edit');return f;}
function stamp(s){const ms=Math.round(s*1000),h=Math.floor(ms/3600000),m=Math.floor(ms/60000)%60,ss=Math.floor(ms/1000)%60;return [h,m,ss].map(x=>String(x).padStart(2,'0')).join(':')+','+String(ms%1000).padStart(3,'0');}
async function doctor(){console.log('Node',process.version);console.log('Chrome',getChrome()||'Playwright-managed browser required');await mediaPrereq();referenceSources();console.log('Dependencies exist. This is not a visual quality pass.');}
try{
 if(mode==='reference')await reference();else if(mode==='render')await render();else if(mode==='assemble')await assemble();else if(mode==='doctor')await doctor();else console.log('Commands: doctor | reference [--stills-only] | render [--shot S03] [--profile review|detail|final] | assemble [--profile review|final]\n--episode episodes/.../episode.json; --allow-software is explicit diagnostic only.');
}catch(e){console.error('BLOCKED:',e.message);process.exitCode=1;}

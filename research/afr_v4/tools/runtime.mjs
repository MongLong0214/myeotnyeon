import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import os from 'node:os';
import {spawn,execFileSync} from 'node:child_process';
import {assert,inside,rejectLinks,safeOutput,atomicWrite,sha} from '../src/core.mjs';
export function command(exe,args,options={}){
 return new Promise((resolve,reject)=>{const p=spawn(exe,args,{shell:false,windowsHide:true,stdio:['ignore','pipe','pipe'],...options});
  let stdout='',stderr='';p.stdout?.on('data',d=>stdout+=d);p.stderr?.on('data',d=>{stderr=(stderr+d).slice(-200000);});
  p.on('error',reject);p.on('close',code=>code===0?resolve({stdout,stderr}):reject(new Error(`${exe} exited ${code}\n${stderr.slice(-3000)}`)));
 });
}
export function getChrome(){
 const specified=process.env.CHROME_PATH;
 if(specified){assert(fs.existsSync(specified),'CHROME_PATH not found');return specified;}
 const p=process.platform==='win32'?[`${process.env.PROGRAMFILES}/Google/Chrome/Application/chrome.exe`,`${process.env['PROGRAMFILES(X86)']}/Microsoft/Edge/Application/msedge.exe`]:process.platform==='darwin'?['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge']:['/usr/bin/chromium','/usr/bin/google-chrome','/usr/bin/chromium-browser'];
 return p.find(x=>fs.existsSync(x));
}
export async function server(root){
 const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg','.wav':'audio/wav'};
 const s=http.createServer((req,res)=>{
  try{const u=new URL(req.url,'http://localhost');if(u.pathname==='/favicon.ico'){res.statusCode=204;res.end();return;}let rel=decodeURIComponent(u.pathname).replace(/^\/+/, '');if(!rel)rel='web/index.html';
   // Bind localhost only, disallow traversals, hidden files and symlink escapes.
   assert(!rel.split('/').some(x=>x.startsWith('.')),'Forbidden');const f=path.resolve(root,rel);
   assert(inside(root,f),'Forbidden');const real=fs.realpathSync(f);assert(inside(root,real),'Forbidden');
   assert(fs.statSync(real).isFile(),'Not file');res.setHeader('Content-Type',mime[path.extname(f)]||'application/octet-stream');res.setHeader('Cache-Control','no-store');fs.createReadStream(real).pipe(res);
  }catch{res.statusCode=404;res.end('Not found');}
 });
 await new Promise(r=>s.listen(0,'127.0.0.1',r));
 return {url:`http://127.0.0.1:${s.address().port}`,close:()=>new Promise(r=>s.close(r))};
}
export function lockOutput(root,relative){
 const p=safeOutput(root,relative);fs.mkdirSync(path.dirname(p),{recursive:true});
 let fd;try{fd=fs.openSync(p,'wx');}catch(e){if(e.code==='EEXIST')throw new Error(`Output is locked: ${p}. Do not delete while another job is running. After a crash, confirm the owner process has stopped, then remove this lock only.`);throw e;}
 fs.writeSync(fd,JSON.stringify({pid:process.pid,host:os.hostname(),at:new Date().toISOString()}));fs.closeSync(fd);
 return ()=>{rejectLinks(p);if(fs.existsSync(p)){const v=JSON.parse(fs.readFileSync(p));if(v.pid===process.pid&&v.host===os.hostname())fs.unlinkSync(p);}};
}
export async function openBrowser({allowSoftware=false}={}){
 const {chromium}=await import('playwright');const executablePath=getChrome();
 const args=['--disable-background-timer-throttling','--disable-renderer-backgrounding'];
 if(process.env.FACTORY_NO_SANDBOX==='1')args.push('--no-sandbox');
 if(allowSoftware)args.push('--use-angle=swiftshader','--enable-unsafe-swiftshader');
 const browser=await chromium.launch({headless:true,executablePath,args});
 return browser;
}
export async function probe(file){
 const {stdout}=await command(process.env.FFPROBE||'ffprobe',['-v','error','-show_streams','-show_format','-of','json',file]);return JSON.parse(stdout);
}
export async function verifyVideo(file,{width,height,fps,frames,audio=false}){
 const p=await probe(file),v=p.streams.find(x=>x.codec_type==='video'),a=p.streams.find(x=>x.codec_type==='audio');
 assert(v,`No video: ${file}`);const [n,d]=v.avg_frame_rate.split('/').map(Number);
 assert(v.width===width&&v.height===height&&Math.abs(n/d-fps)<1e-6,'Video dimensions/fps mismatch');
 assert(Number(v.nb_frames)===frames,'Video frame count mismatch');assert(!audio||a,'Required audio missing');
 if(a)assert(Math.abs(Number(a.duration||p.format.duration)-frames/fps)<0.1,'Audio duration mismatch');
 await command(process.env.FFMPEG||'ffmpeg',['-v','error','-xerror','-i',file,'-f','null','-']);return p;
}
export async function encodeFrames(root,dir,{width,height,fps,frames},signal){
 const final=safeOutput(root,path.join(dir,'picture.mp4'));const temp=safeOutput(root,path.join(dir,`picture.${process.pid}.tmp.mp4`));
 try{
  await command(process.env.FFMPEG||'ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate',String(fps),'-start_number','0','-i',path.join(root,dir,'frames/f_%06d.png'),'-frames:v',String(frames),'-an','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1','-color_range','tv','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-colorspace','bt709','-color_trc','iec61966-2-1','-movflags','+faststart',temp],{signal});
  await verifyVideo(temp,{width,height,fps,frames});rejectLinks(final);fs.renameSync(temp,final);return final;
 }finally{if(fs.existsSync(temp))fs.unlinkSync(temp);}
}

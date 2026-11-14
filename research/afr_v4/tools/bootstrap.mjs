import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {assert,gitBlob,rejectLinks,atomicWrite} from '../src/core.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const lock=JSON.parse(fs.readFileSync(path.join(root,'reference.lock.json')));
const dest=path.join(root,'vendor/todai');
function verify(dir){
 for(const [f,h]of Object.entries(lock.gitBlobs))assert(gitBlob(fs.readFileSync(path.join(dir,f)))===h,`Reference mismatch: ${f}`);
 assert(fs.readFileSync(path.join(dir,'LICENSE'),'utf8').startsWith('MIT License'),'Unexpected upstream license');
 for(const f of ['vendor/three/build/three.module.js','index.html','src/clawd/clawd.glb'])assert(fs.existsSync(path.join(dir,f)),`Incomplete source: ${f}`);
}
try{
 rejectLinks(dest);
 if(fs.existsSync(dest)){verify(dest);console.log('Pinned source already present; no changes.');process.exit(0);}
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 const tmp=fs.mkdtempSync(path.join(root,'vendor/.todai-'));
 try{
  const git=(...a)=>execFileSync('git',a,{cwd:tmp,stdio:'inherit',timeout:180000,windowsHide:true});
  git('init');git('config','core.autocrlf','false');git('remote','add','origin',lock.repository);
  git('fetch','--depth=1','origin',lock.commit);git('checkout','--detach','FETCH_HEAD');
  const rev=execFileSync('git',['rev-parse','HEAD'],{cwd:tmp,encoding:'utf8'}).trim();assert(rev===lock.commit,'Wrong reference commit');
  verify(tmp);fs.rmSync(path.join(tmp,'.git'),{recursive:true,force:true});
  fs.renameSync(tmp,dest);
  atomicWrite(root,'vendor/SOURCE.json',JSON.stringify({repository:lock.repository,commit:rev,checkedAt:new Date().toISOString()},null,2));
  console.log('Exact reference source installed. No upstream files modified.');
 }finally{if(fs.existsSync(tmp))fs.rmSync(tmp,{recursive:true,force:true});}
}catch(e){console.error('SETUP BLOCKED:',e.message);console.error('No substitute renderer or placeholder has been generated.');process.exitCode=1;}

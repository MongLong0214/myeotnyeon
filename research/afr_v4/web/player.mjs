import * as THREE from 'three';
import * as A from '/vendor/todai/src/anime.js';
import {createWorld} from './world.mjs';
const q=new URLSearchParams(location.search);
const width=Number(q.get('width')||360),height=Number(q.get('height')||640);
if(!Number.isInteger(width)||!Number.isInteger(height)||width<64||height<64||width>4096||height>4096)throw new Error('Invalid render size');
window.factoryErrors=[];
window.addEventListener('error',e=>window.factoryErrors.push(e.message));
window.ready=(async()=>{
 const epPath=q.get('episode')||'episodes/one_step_behind/episode.json';
 if(!/^episodes\/[a-zA-Z0-9_/-]+\.json$/.test(epPath))throw new Error('Invalid episode path');
 const res=await fetch('/'+epPath);if(!res.ok)throw new Error(`Episode not found ${res.status}`);const episode=await res.json();
 const shot=episode.shots.find(s=>s.id===(q.get('shot')||episode.shots[0].id));if(!shot)throw new Error('Unknown shot');
 const modulePath=shot.module;
 if(!modulePath.startsWith('episodes/')||modulePath.includes('..'))throw new Error('Invalid shot module');
 const mod=await import('/'+modulePath);
 const stage=A.createAnimeRenderer({width,height,samples:4});document.body.appendChild(stage.canvas);
 const world=createWorld({THREE,A,renderer:stage.renderer,post:stage.post,width,height,episode});
 const gl=stage.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');
 const gpu=ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 window.factoryInfo={width,height,fps:episode.fps,frames:shot.frames,gpu,kit:A.KIT_VERSION,role:'original-unreviewed',episode:episode.id,shot:shot.id};
 window.renderFrame=(frame)=>{
  if(!Number.isInteger(frame)||frame<0||frame>=shot.frames)throw new Error('Frame outside shot');
  // Every pose is rebuilt from absolute time, not elapsed playback time.
  const t=frame/episode.fps;
  world.reset();mod.pose(world,t,shot.params||{},episode.fps);
  world.finish(t);
  return stage.canvas.toDataURL('image/png');
 };
 window.frameMeta=(frame)=>({episode:episode.id,shot:shot.id,frame,seconds:frame/episode.fps,kind:'actual_scene'});
 if(!q.has('capture')){
  let frame=0;setInterval(()=>{window.renderFrame(frame);frame=(frame+1)%shot.frames;},1000/episode.fps);
 }
 return true;
})().catch(e=>{document.querySelector('#error').textContent=e.stack;window.factoryErrors.push(String(e));throw e;});

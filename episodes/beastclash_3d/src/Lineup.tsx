import React,{useEffect,useLayoutEffect,useState} from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig,delayRender,continueRender} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';
import {Beast,loadBeast,pose} from './toon';
export const polarTint=(c:THREE.Color)=>{const l=.3*c.r+.6*c.g+.1*c.b,t=Math.min(1,l/.18),v=.84+.16*t; c.setRGB(v,v*.985,v*.94);};
export const crocTint=(c:THREE.Color)=>{const l=.3*c.r+.6*c.g+.1*c.b; c.setRGB(.18+.5*l,.38+.55*l,.16+.3*l);};
const SPEC:[string,any,string][]=[
 ['bear',{length:2.6,yaw:Math.PI/2,outline:.022,tint:polarTint},'B'],
 ['alligator',{length:3.6,yaw:Math.PI/2,outline:.022,tint:crocTint},'B'],
 ['panther',{length:2.4,yaw:Math.PI/2,outline:.022},'A'],
 ['snake',{length:1.6,yaw:Math.PI/2,outline:.018},'Attack'],
 ['shark',{length:3.0,yaw:Math.PI/2,outline:.022},'Swim']];
const Inner:React.FC<{bs:Beast[]}> = ({bs})=>{ const f=useCurrentFrame();
 useLayoutEffect(()=>{ bs.forEach((b,i)=>{ const k=Object.keys(b.clips).find(k=>k.includes(SPEC[i][2]))||Object.keys(b.clips)[0]; pose(b,k,f/30/b.clips[k].duration); b.root.position.set(0,3.7-i*1.85,0); b.root.rotation.y=-.5; }); },[f,bs]);
 return <><ambientLight intensity={1.5}/><directionalLight position={[3,6,5]} intensity={2.2}/>{bs.map((b,i)=><primitive key={i} object={b.root}/>)}</>; };
export const Lineup:React.FC=()=>{ const {width,height}=useVideoConfig(); const [bs,set]=useState<Beast[]|null>(null); const [h]=useState(()=>delayRender('glb'));
 useEffect(()=>{ Promise.all(SPEC.map(([n,o])=>loadBeast(n,o))).then(b=>{console.log(b.map(x=>Object.keys(x.clips).join('/')+' '+x.size.toArray().map(v=>v.toFixed(2)).join('x')).join(' ; ')); set(b); continueRender(h);}); },[h]);
 return <AbsoluteFill style={{background:'#bcd6e6'}}>{bs&&<ThreeCanvas width={width} height={height} flat orthographic camera={{position:[0,.5,10],zoom:200}}><Inner bs={bs}/></ThreeCanvas>}</AbsoluteFill>; };

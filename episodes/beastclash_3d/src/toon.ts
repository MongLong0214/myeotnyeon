import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import {GLB} from './_assets';

export const INK=0x1b1b26;
let grad:THREE.DataTexture|null=null;
export const gradientMap=()=>{ if(!grad){ grad=new THREE.DataTexture(new Uint8Array([120,120,120,255, 205,205,205,255, 255,255,255,255]),3,1,THREE.RGBAFormat); grad.minFilter=grad.magFilter=THREE.NearestFilter; grad.generateMipmaps=false; grad.needsUpdate=true;} return grad; };

export type Beast={root:THREE.Group; mixer:THREE.AnimationMixer; clips:Record<string,THREE.AnimationClip>; actions:Record<string,THREE.AnimationAction>; meshes:THREE.Mesh[]; size:THREE.Vector3};
type Opt={length:number; yaw:number; outline:number; tint?:(c:THREE.Color)=>void};

// position-merged smooth normals so the inverted hull does not crack on hard edges
const smoothNormals=(g:THREE.BufferGeometry)=>{
  const p=g.attributes.position, n=g.attributes.normal, acc=new Map<string,number[]>(), key=(i:number)=>`${p.getX(i).toFixed(4)},${p.getY(i).toFixed(4)},${p.getZ(i).toFixed(4)}`;
  for(let i=0;i<p.count;i++){const k=key(i),a=acc.get(k)||[0,0,0]; a[0]+=n.getX(i);a[1]+=n.getY(i);a[2]+=n.getZ(i); acc.set(k,a);}
  const out=new Float32Array(p.count*3);
  for(let i=0;i<p.count;i++){const a=acc.get(key(i))!,l=Math.hypot(a[0],a[1],a[2])||1; out.set([a[0]/l,a[1]/l,a[2]/l],i*3);}
  g.setAttribute('oN',new THREE.BufferAttribute(out,3));
};
const hullMat=(t:number)=>{ const m=new THREE.MeshBasicMaterial({color:INK,side:THREE.BackSide});
  m.onBeforeCompile=s=>{ s.uniforms.uT={value:t}; s.vertexShader='attribute vec3 oN;\nuniform float uT;\n'+s.vertexShader.replace('#include <skinning_vertex>','transformed += oN*uT;\n#include <skinning_vertex>'); };
  return m; };

const parse=(name:string)=>new Promise<any>((res,rej)=>{ const bin=Uint8Array.from(atob(GLB[name]),c=>c.charCodeAt(0)); new GLTFLoader().parse(bin.buffer,'',res,rej); });

export const loadBeast=async(name:string,o:Opt):Promise<Beast>=>{
  const gltf=await parse(name); const scene:THREE.Object3D=gltf.scene; const meshes:THREE.Mesh[]=[];
  scene.traverse(x=>{ if((x as THREE.Mesh).isMesh) meshes.push(x as THREE.Mesh); });
  scene.updateMatrixWorld(true);
  const box=new THREE.Box3(); for(const m of meshes){ if(m.morphTargetInfluences){const b=new THREE.Box3().setFromBufferAttribute(m.geometry.attributes.position as THREE.BufferAttribute); box.union(b.applyMatrix4(m.matrixWorld));} else box.expandByObject(m); }
  const size=box.getSize(new THREE.Vector3()), c=box.getCenter(new THREE.Vector3());
  const s=o.length/Math.max(size.x,size.z);
  for(const m of meshes){
    const g=m.geometry as THREE.BufferGeometry; if(!g.attributes.normal) g.computeVertexNormals(); smoothNormals(g);
    const col=g.attributes.color as THREE.BufferAttribute|undefined;
    if(col&&o.tint){const k=new THREE.Color(); for(let i=0;i<col.count;i++){k.fromBufferAttribute(col,i); o.tint(k); col.setXYZ(i,k.r,k.g,k.b);} }
    const conv=(old:any)=>new THREE.MeshToonMaterial({color:col?0xffffff:old.color, vertexColors:!!col, gradientMap:gradientMap()});
    m.material=Array.isArray(m.material)?m.material.map(conv):conv(m.material);
    m.frustumCulled=false;
    const ws=new THREE.Vector3(); m.getWorldScale(ws);
    const hull=m.clone() as THREE.Mesh; hull.material=hullMat(o.outline/(s*ws.x)); hull.frustumCulled=false;
    if(m.morphTargetInfluences) hull.morphTargetInfluences=m.morphTargetInfluences;
    m.parent!.add(hull);
  }
  const inner=new THREE.Group(); inner.add(scene); scene.position.set(-c.x,-box.min.y,-c.z); inner.scale.setScalar(s); inner.rotation.y=o.yaw;
  const root=new THREE.Group(); root.add(inner);
  const mixer=new THREE.AnimationMixer(scene), clips:Record<string,THREE.AnimationClip>={}, actions:Record<string,THREE.AnimationAction>={};
  for(const cl of gltf.animations as THREE.AnimationClip[]){ const k=cl.name.split(/[|_]/).pop()!; clips[k]=cl; actions[k]=mixer.clipAction(cl); }
  return {root,mixer,clips,actions,meshes,size:size.multiplyScalar(s)};
};
// deterministic pose: one clip at an absolute phase (in cycles)
export const pose=(b:Beast,clip:string,cycles:number)=>{ for(const k in b.actions){const a=b.actions[k]; if(k===clip){a.play(); a.setEffectiveWeight(1); a.time=((cycles%1)+1)%1*b.clips[k].duration;} else a.stop(); } b.mixer.update(0); };

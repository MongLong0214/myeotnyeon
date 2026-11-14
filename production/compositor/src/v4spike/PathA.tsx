import React, { useLayoutEffect, useMemo } from 'react';
import { ThreeCanvas } from '@remotion/three';
import { useThree } from '@react-three/fiber';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { AdditiveBlending, Color, HalfFloatType, Uniform } from 'three';
import { BloomEffect, Effect, EffectComposer, EffectPass, RenderPass } from 'postprocessing';
import { cameraAt, commander, palette as C, recruits, Vec3 } from './scene';
import { Overlay } from './Overlay';

// Local JSX aliases: the runtime-only three package has no bundled TS types.
const Standard = 'meshStandardMaterial' as React.ElementType;
const Basic = 'meshBasicMaterial' as React.ElementType;
const Shader = 'shaderMaterial' as React.ElementType;

const rimVertex = `varying vec3 n; varying vec3 v;
void main(){vec4 p=modelViewMatrix*vec4(position,1.); n=normalize(normalMatrix*normal);v=-p.xyz;gl_Position=projectionMatrix*p;}`;
const rimFragment = `uniform float red; varying vec3 n; varying vec3 v;
void main(){float rim=pow(1.-abs(dot(normalize(n),normalize(v))),2.6);
float side=smoothstep(-.15,.65,n.x);vec3 c=mix(vec3(.12,.38,.9),vec3(1.9,.20,.47),side);
gl_FragColor=vec4(c,rim*mix(.45,red,side));}`;

const Capsule: React.FC<{position: Vec3; scale: Vec3; main: boolean}> = ({position,scale,main}) => <group position={position} scale={scale}>
  <mesh><capsuleGeometry args={[1,1,8,20]}/><Standard color={main?'#486B9D':'#B8BFCD'} roughness={.85} metalness={.05} emissive={C.deepBlue} emissiveIntensity={main?.35:.15}/></mesh>
  <mesh scale={1.012}><capsuleGeometry args={[1,1,8,20]}/><Shader vertexShader={rimVertex} fragmentShader={rimFragment}
    uniforms={{red:{value:main?.6:0}}} transparent depthWrite={false} blending={AdditiveBlending}/></mesh>
</group>;

const Figure: React.FC<{position:Vec3; scale:number; main?:boolean}> = ({position,scale,main=false}) => <group position={position} scale={scale}>
  <Capsule position={[0,1.92,0]} scale={[.14,.15,.145]} main={main}/>
  <Capsule position={[0,1.68,0]} scale={[.085,.075,.085]} main={main}/>
  <Capsule position={[0,1.27,0]} scale={[.265,.25,.18]} main={main}/>
  <Capsule position={[-.34,1.18,0]} scale={[.092,.27,.095]} main={main}/>
  <Capsule position={[.34,1.18,0]} scale={[.092,.27,.095]} main={main}/>
  <Capsule position={[-.13,.49,0]} scale={[.115,.28,.12]} main={main}/>
  <Capsule position={[.13,.49,0]} scale={[.115,.28,.12]} main={main}/>
  <mesh position={[0,.008,0]} rotation={[-Math.PI/2,0,0]} scale={[.7,.32,1]}><circleGeometry args={[1,32]}/><Basic color="#02040A" transparent opacity={.8}/></mesh>
</group>;

// The postprocessing package is used directly. No React postprocessing wrapper
// or useFrame subscription is needed: ThreeCanvas advances each Remotion frame.
// Wrap only the outer render; RenderPass calls the original renderer reentrantly.
const FrameEffects: React.FC = () => {
  const {gl,scene,camera,size} = useThree();
  const f = useCurrentFrame();
  const wide=size.width>size.height;
  const c=cameraAt(f,wide);
  useLayoutEffect(()=>{
    camera.position.set(...c.position);
    camera.lookAt(...c.target);
    camera.updateMatrixWorld();
  },[camera,f,wide]);
  const grade = useMemo(()=>new Effect('V4Duotone', `uniform float frameSeed;
    float hash(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+frameSeed*17.17)*43758.5453);}
    void mainImage(const in vec4 inputColor,const in vec2 uv,out vec4 outputColor){
      float l=dot(inputColor.rgb,vec3(.2126,.7152,.0722));
      vec3 ink=vec3(.0196,.0275,.051);vec3 blue=vec3(.043,.247,.627);
      vec3 red=vec3(.843,.149,.310);vec3 pink=vec3(.965,.651,.698);
      vec3 cool=mix(ink,blue,smoothstep(0.,.45,l));
      cool=mix(cool,vec3(.60,.73,.91),smoothstep(.35,1.,l));
      vec3 warm=mix(ink,red,smoothstep(0.,.5,l));warm=mix(warm,pink,smoothstep(.35,1.,l));
      float mask=smoothstep(.015,.18,inputColor.r-inputColor.b);
      vec3 color=mix(cool,warm,mask*.6);
      float edge=pow(clamp(length((uv-vec2(.5,.53))*vec2(1.,.85))*1.3,0.,1.),2.);
      color*=1.-.35*edge;color*=1.-.55*smoothstep(.22,0.,uv.y);
      // Linear-space dither, about 3–4% after the display transfer function.
      color+=(hash(gl_FragCoord.xy)-.5)*.006;
      outputColor=vec4(max(color,vec3(0.)),1.);
    }`, {uniforms:new Map([['frameSeed',new Uniform(f)]])}),[]);
  useLayoutEffect(()=>{ grade.uniforms.get('frameSeed')!.value=f; },[f,grade]);
  useLayoutEffect(()=>{
    const composer=new EffectComposer(gl,{frameBufferType:HalfFloatType,multisampling:0});
    composer.addPass(new RenderPass(scene,camera));
    composer.addPass(new EffectPass(camera,new BloomEffect({luminanceThreshold:.6,luminanceSmoothing:.15,intensity:.55,mipmapBlur:true})));
    composer.addPass(new EffectPass(camera,grade));
    composer.setSize(size.width,size.height);
    const original=gl.render;
    let inside=false;
    gl.render=function(...args:Parameters<typeof original>){
      if(inside) return original.apply(gl,args);
      inside=true;
      try { composer.render(0); } finally { inside=false; }
    };
    return ()=>{gl.render=original;composer.dispose();};
  },[gl,scene,camera,size.width,size.height,grade]);
  return null;
};

const World:React.FC=()=> <>
  <color attach="background" args={[C.ink]}/>
  <fog attach="fog" args={[C.navy,10,31]}/>
  <hemisphereLight args={['#729EFF','#080B15',1.05]}/>
  <directionalLight position={[-5,6,1]} color="#739CFF" intensity={2.2}/>
  <spotLight position={[3,3,-1]} color={C.red} intensity={.6} angle={1.1} penumbra={.7} decay={0} target-position={commander}/>
  <mesh rotation={[-Math.PI/2,0,0]} position={[0,-.025,-3]}><planeGeometry args={[38,48]}/><Standard color="#172C50" roughness={.9}/></mesh>
  <gridHelper args={[32,20,'#365888','#284568']} position={[0,.005,-3]}/>
  <mesh position={[0,.8,-12.2]}><boxGeometry args={[14,1.6,.25]}/><Standard color="#172A4C"/></mesh>
  <mesh position={[-3,.012,-2]} rotation={[-Math.PI/2,0,0]}><planeGeometry args={[.045,26]}/><Basic color="#4172B8"/></mesh>
  <mesh position={[3,.75,2.5]}><boxGeometry args={[.2,1.5,.2]}/><Standard color="#121A2A" emissive={C.red} emissiveIntensity={.6}/></mesh>
  {recruits.map((position,i)=><Figure key={i} position={position} scale={.82}/>)}
  <Figure position={commander} scale={1.25} main/>
  <FrameEffects/>
</>;

export const PathA:React.FC=()=>{
  const f=useCurrentFrame();
  const {width,height}=useVideoConfig();
  const c=cameraAt(f,width>height);
  return <AbsoluteFill style={{background:C.ink}}>
    <ThreeCanvas width={width} height={height} dpr={1} camera={{position:c.position,fov:c.fov,near:.1,far:80}}
      gl={{antialias:true,alpha:false,preserveDrawingBuffer:true}} onCreated={({gl})=>{gl.setClearColor(new Color(C.ink));}}>
      <World/>
    </ThreeCanvas>
    <Overlay/>
  </AbsoluteFill>;
};

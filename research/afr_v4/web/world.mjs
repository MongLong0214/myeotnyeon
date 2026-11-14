import {blink,elbowFor,mix,ease} from '../src/motion.mjs';

// Original scene/characters; reference code is used for rendering, not its story or mascot.
// All poses are explicit. Supported scope: this human rig and this sunny-courtyard set.
export function createWorld({THREE:T,A,renderer,post,width,height,episode}){
 const rand=A.rng(episode.seed||1);
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(34,width/height,.05,200);
 const V=(x=0,y=0,z=0)=>new T.Vector3(x,y,z);
 const rig=A.createRig();
 const res=new T.Vector2(width,height), ink=A.outlineMaterial({rig,px:2.2*height/1920,res,color:0x342741});
 const paint=(color,extra={})=>A.paintMaterial({rig,color,ambLit:.38,lock:.12,...extra});
 const cel=(color,extra={})=>A.toonMaterial({rig,color,mask:0,brush:.055,ambLit:.2,hiAmt:.35,lock:.40,...extra});
 const M={stone:paint(0xd6b88e),wall:paint(0xe4c7aa),wood:paint(0x86645e),dark:paint(0x47475f),leaf:paint(0x65907e),petal:paint(0xefaa98),blue:paint(0x7294aa),gold:paint(0xf0c782)};
 function mesh(g,m,p=V(),scale=null,outline=false,parent=scene){const o=new T.Mesh(g,m);o.position.copy(p);if(scale)o.scale.copy(scale);parent.add(o);if(outline)A.addOutline(o,ink);return o;}
 function box(s,p,m,parent=scene,outline=false){return mesh(new T.BoxGeometry(...s),m,V(...p),null,outline,parent);}
 const sphere=(r,p,m,scale=null,parent=scene,outline=false)=>mesh(new T.SphereGeometry(r,32,20),m,V(...p),scale?V(...scale):null,outline,parent);
 const rod=(r,a,b,m,parent=scene)=>{const mid=a.clone().add(b).multiplyScalar(.5),d=b.clone().sub(a);const o=mesh(new T.CylinderGeometry(r,r,d.length(),12),m,mid,null,false,parent);o.quaternion.setFromUnitVectors(V(0,1,0),d.normalize());return o;};
 // Backplate sky uses actual shader colour, no downloaded/generated image plate.
 const sky=new T.Mesh(new T.SphereGeometry(100,48,24),new T.ShaderMaterial({side:T.BackSide,depthWrite:false,uniforms:{top:{value:new T.Color(0x536eaf)},bottom:{value:new T.Color(0xffd6a4)}},vertexShader:'varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec3 p;uniform vec3 top,bottom;void main(){float u=smoothstep(-.08,.72,normalize(p).y);gl_FragColor=vec4(mix(bottom,top,u),1.);}'}));scene.add(sky);
 box([35,.16,35],[0,-.1,0],M.stone);
 // Courtyard geometry: layered façades, window recesses, canopy, tiled roof, greenery.
 for(let i=-3;i<=3;i++){
  const x=i*3.9,z=-6.8-Math.abs(i)*.3,h=4.1+(i%2===0?.6:0);
  box([3.75,h,1.6],[x,h/2,z],i%2===0?M.wall:paint(0xcdbbb2));
  const roof=mesh(new T.ConeGeometry(2.8,.65,4),M.wood,V(x,h+.25,z));roof.rotation.y=Math.PI/4;
  for(let j=-1;j<=1;j++){box([.72,1.25,.05],[x+j*1.03,2.8,z+.83],M.dark);box([.57,1.05,.07],[x+j*1.03,2.8,z+.87],M.blue);box([.035,1.1,.08],[x+j*1.03,2.8,z+.92],M.gold);}
  box([1.15,2,.08],[x,1,z+.85],M.wood);
 }
 // Street-level awning with a readable alternating pattern, no UI/information boards.
 for(let i=0;i<12;i++){
  const o=box([.29,.08,1.25],[-2.2+i*.29,2.65,-5.1],i%2?paint(0xefc7ad):paint(0x975d69));o.rotation.x=.15;
 }
 for(const x of [-4.8,4.1]){
  rod(.10,V(x,0,-2),V(x,3.7,-2),M.wood);
  for(let i=0;i<7;i++)sphere(.9,[x+Math.sin(i*2.4)*.62,3.5+Math.sin(i*.7)*.5,-2+Math.cos(i*2.4)*.62],M.leaf,[1.1,.75,1]);
  const pot=mesh(new T.CylinderGeometry(.42,.29,.60,24),paint(0xb97665),V(x,.3,-1.5));
  for(let j=0;j<8;j++)sphere(.10,[x+Math.cos(j)*.28,.77+Math.sin(j*3)*.1,-1.5+Math.sin(j)*.25],M.petal);
 }
 // Bench and contact details.
 for(let i=0;i<5;i++)box([2.6,.09,.11],[-2.6,.62,-1.5+i*.13],M.wood);
 for(const x of [-3.55,-1.65]){box([.10,.63,.65],[x,.29,-1.25],M.dark);box([.10,1.25,.10],[x,.92,-1.62],M.dark);}
 for(let i=0;i<3;i++)box([2.6,.10,.09],[-2.6,.98+i*.18,-1.65],M.wood);
 // Small stones provide depth and a stable visual scale.
 for(let i=0;i<36;i++){const x=((i*7)%17)-8+rand()*.08,z=-3+((i*11)%13)*.58+rand()*.08;box([.48,.007,.24],[x,.005,z],paint(i%3?0xc5ac91:0xdcc4a2));}
 const actors={};
 function actor(name,{coat,hair,skin,scarf,scale=1,x=0,z=0}){
  const root=new T.Group();root.name=name;root.scale.setScalar(scale);root.position.set(x,0,z);scene.add(root);
  const cm=cel(coat),sm=cel(skin),hm=cel(hair),boots=cel(0x333347),sc=cel(scarf);
  const body=new T.Group();root.add(body);
  const torso=mesh(new T.CylinderGeometry(.20,.29,.70,32),cm,V(0,1.09,0),V(1,1,.76),true,body);
  sphere(.25,[0,1.38,0],cm,[1,.6,.82],body,true);
  box([.018,.58,.018],[0,1.12,.196],cel(0xe8c9ad),body);
  for(let i=0;i<3;i++)sphere(.025,[.075,1.22-i*.13,.20],cel(0xe9c887),null,body);
  const neck=sphere(.09,[0,1.54,0],sm,[1,1,1],body);
  const head=new T.Group();head.position.set(0,1.80,0);body.add(head);
  sphere(.32,[0,0,0],sm,[.91,1,.88],head,true);
  sphere(.329,[0,.075,-.055],hm,[.99,.96,.87],head,true);
  // Front fringe is sculpted from curved volumes; back shell leaves the face exposed.
  for(let i=0;i<5;i++){const bang=sphere(.13,[-.21+i*.105,.18-.02*Math.abs(i-2),.20],hm,[.95,.74,.55],head,true);bang.rotation.z=(i-2)*.17;}
  for(const side of [-1,1])sphere(.095,[side*.279,-.01,.01],sm,[.5,.85,.65],head,true);
  const eyes=[];
  for(const side of [-1,1]){
   const e=new T.Group();e.position.set(side*.108,.015,.26);head.add(e);
   sphere(.057,[0,0,0],cel(0xfff4e5),[.75,1,.36],e);
   const pupil=sphere(.035,[0,-.004,.022],cel(0x302e3a),[.72,1,.5],e);
   sphere(.010,[-.009,.015,.038],cel(0xfff6dd),null,e);eyes.push(e);
   const brow=box([.083,.015,.018],[side*.109,.105,.277],hm,head);brow.rotation.z=side*.12;
  }
  sphere(.045,[0,-.052,.282],sm,[.65,.65,.8],head);
  const mouth=mesh(new T.TorusGeometry(.049,.008,8,20,Math.PI),cel(0x713e47),V(0,-.135,.258),null,false,head);mouth.rotation.z=Math.PI;
  const scarfBand=mesh(new T.TorusGeometry(.15,.07,12,32),sc,V(0,1.51,.02),null,true,body);scarfBand.rotation.x=Math.PI/2;
  const scarfTail=box([.13,.38,.045],[.10,1.28,.24],sc,body,true);scarfTail.rotation.z=-.11;
  const arms=[],legs=[];
  for(const side of [-1,1]){
   const shoulder=V(side*.245,1.39,0),upper=mesh(new T.CylinderGeometry(.078,.066,1,12),cm,V(),null,true,root),lower=mesh(new T.CylinderGeometry(.066,.055,1,12),cm,V(),null,true,root),hand=sphere(.070,[side*.32,.8,.1],sm,[.7,1,.65],root,true);
   arms.push({side,shoulder,upper,lower,hand});
   const thigh=mesh(new T.CylinderGeometry(.09,.075,1,12),cel(0x4b526d),V(),null,true,root),shin=mesh(new T.CylinderGeometry(.075,.065,1,12),cel(0x4b526d),V(),null,true,root),shoe=sphere(.115,[side*.13,.10,.05],boots,[.8,.65,1.5],root,true);legs.push({side,thigh,shin,shoe});
  }
  function bone(o,a,b){o.position.copy(a).add(b).multiplyScalar(.5);const d=b.clone().sub(a);o.scale.y=d.length();o.quaternion.setFromUnitVectors(V(0,1,0),d.normalize());}
  const api={root,body,head,eyes,mouth,arms,legs,scarfTail,scale,baseX:x,baseZ:z,
   pose(p={}){
    root.position.set(p.x??x,0,p.z??z);root.rotation.y=p.yaw??0;
    body.position.y=p.bob??0;body.rotation.z=p.lean??0;head.rotation.set(p.nod??0,p.look??0,p.tilt??0);
    const open=blink(p.time||0,name==='reader'?1.1:0);eyes.forEach(e=>e.scale.y=Math.max(.08,open));mouth.scale.set(1,p.smile??1,1);scarfTail.rotation.z=-.11+.025*Math.sin((p.time||0)*2.1);
    for(const arm of arms){const s=arm.shoulder.clone(),h=V(arm.side*.32,.86,.07);const custom=arm.side<0?p.leftHand:p.rightHand;if(custom)h.copy(V(...custom));
     const elbow=elbowFor(s,h,.29,.29,V(arm.side*.50,1.12,-.2));bone(arm.upper,s,elbow);bone(arm.lower,elbow,h);arm.hand.position.copy(h);
    }
    for(const leg of legs){const phase=leg.side<0?p.step?.left:p.step?.right;const localX=phase?(phase.x-(p.x??x))/scale:0;
     const foot=V(leg.side*.13+localX,.10+(phase?.lift||0),.03),hip=V(leg.side*.13,.80,0),knee=hip.clone().lerp(foot,.50).add(V(0,0,.12));bone(leg.thigh,hip,knee);bone(leg.shin,knee,foot);leg.shoe.position.copy(foot);}
   }
  };api.pose();actors[name]=api;return api;
 }
 const hero=actor('hero',{coat:0xa94f63,hair:0x313346,skin:0xeab995,scarf:0xe9b968,x:-.45,z:0});
 const reader=actor('reader',{coat:0x406e82,hair:0x61504c,skin:0xeac6a1,scarf:0xb9bd8d,scale:.88,x:.52,z:-.48});
 // Book anchored in reader coordinates. Hands grasp the same fixed corners.
 const book=new T.Group();book.position.set(0,1.20,.40);book.rotation.x=-.45;reader.root.add(book);
 box([.62,.045,.37],[0,0,0],cel(0x6e5d8b),book,true);
 const paper=cel(0xffedc4);box([.58,.030,.33],[0,.038,0],paper,book);
 box([.014,.044,.34],[0,.063,0],cel(0xb1a18a),book);
 for(let i=0;i<5;i++)for(const x of [-.15,.15])box([.20,.002,.008],[x,.055,-.105+i*.05],cel(0xada08f),book);
 // Art-directed cast shadow tied to the light direction and hero position.
 // This is a drawn shadow mesh, not a general physically simulated shadow solver.
 const shadeMat=A.maskMat(new T.MeshBasicMaterial({color:0x756b98,transparent:true,opacity:.31,depthWrite:false}),1);
 const shadow=new T.Group();scene.add(shadow);
 const sh=mesh(new T.CircleGeometry(1,64),shadeMat,V(.7,.015,-.42),V(1.15,1.05,1),false,shadow);sh.rotation.x=-Math.PI/2;sh.rotation.z=-.50;
 const sun=mesh(new T.SphereGeometry(1.1,32,16),cel(0xffe1a7,{emissive:0xffb65b,emisK:1.5}),V(-12,13,-30));
 rig.key(V(-.6,.65,.45),0xffdcab,.95).amb(0x8d9cb8,0x7d6377,.85).rim(V(.6,.35,-.5),0xffdbb7,.5).fog(0xd6b4a7,13,45,{max:.77});
 post.set({expo:episode.lookSettings?.exposure??1.1,sat:episode.lookSettings?.saturation??1.02,knee:.78,vignette:.17,grain:.012,paper:.035,halation:.10,ca:.4,
  paint:{k:1,radius:Math.max(1,3.5*height/1920),q:8,hard:1,aniso:1,stroke:.055,strokeLen:1.4,wobble:.8*height/1920,vary:.08,hue:.06,paper:.045},
  bloom:{strength:.28,radius:.5,threshold:1.1},rays:{on:false}});
 const world={scene,camera,rig,hero,reader,book,paper,shadow,post,
  reset(){hero.pose({time:0});reader.pose({time:0,leftHand:[-.22,1.18,.37],rightHand:[.22,1.18,.37]});shadow.position.x=0;paper.uniforms.uBase.value.setHex(0xffedc4);camera.position.set(4,3.2,8);camera.lookAt(0,1.15,0);camera.fov=34;},
  frame({heroX=-.45,readerX=.52,look=0,nod=0,smile=1,time=0,step=null,readerStep=null,reveal=0,wide=0,lean=0}={}){
   hero.pose({x:heroX,look,nod,smile,time,step,lean});reader.pose({x:readerX,look:-.07,nod:.16,smile:1,time,step:readerStep,leftHand:[-.22,1.18,.37],rightHand:[.22,1.18,.37]});
   shadow.position.x=heroX+.45;
   const shade=1-Math.min(1,Math.abs(readerX-heroX-.97)*1.7);paper.uniforms.uBase.value.setHex(shade>.5?0xd9d8d1:0xffedc4);
   const target=new T.Vector3(mix(.05,readerX,reveal),mix(1.12,1.22,reveal),mix(0,.08,reveal));
   camera.position.set(mix(4+wide*.8,readerX+.9,reveal),mix(3.2+wide*.3,2.05,reveal),mix(8+wide,2.2,reveal));camera.lookAt(target);camera.updateProjectionMatrix();
  },
  finish(t){scene.updateMatrixWorld(true);rig.update(t);post.render(scene,camera,t);}
 };world.reset();return world;
}

import React from 'react';

export const ink='#17152b', paper='#fff5db';
export const ease=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)};
export const between=(f:number,a:number,b:number)=>ease((f-a)/Math.max(1,b-a));
export type Angle='profile'|'quarter'|'rear';
export type ActorRole='judge'|'lawyer'|'commander'|'deputy'|'officer'|'recruit'|'medic'|'reader'|'parent'|'visitor';
type Props={x:number;y:number;s?:number;role:ActorRole;angle?:Angle;face?:'left'|'right';gaze?:number;head?:number;bow?:number;present?:number;read?:number;reach?:number;hand?:[number,number];hideArm?:boolean;stride?:number;mouth?:number;family?:'mother'|'father';jacket?:string};
const colors:Record<ActorRole,string>={judge:'#30273c',lawyer:'#5968a5',commander:'#5a5b6a',deputy:'#848292',officer:'#4c6345',recruit:'#648257',medic:'#d4eee1',reader:'#77b9b0',parent:'#56a698',visitor:'#596b89'};

// Each angle has its own silhouette, shoulders, limbs and head construction.
// There is no face-crop, horizontal squash, idle oscillation or camera jitter.
export const AngleActor=({x,y,s=1,role,angle='quarter',face='right',gaze=0,head=0,bow=0,present=0,read=0,reach=0,hand,hideArm=false,stride=0,mouth=0,family,jacket}:Props)=>{
 const side=angle==='profile',rear=angle==='rear',color=jacket??(family==='mother'?'#56e4c1':family==='father'?'#77b9b0':colors[role]);
 const anonymous=['commander','deputy','officer','recruit','parent','visitor'].includes(role);
 const skin=anonymous?'#797f79':'#efb888',hair=role==='judge'?'#e4d9d3':role==='recruit'||role==='officer'?'#3f6551':'#42334d';
 const hx=hand?.[0]??(side?35:57)+present*100+reach*95-read*28;
 const hy=hand?.[1]??-147-present*67-reach*30-read*82;
 const arm=(front:boolean)=>{
  const sx=side?(front?25:-22):(front?44:-42),sy=side?-265:-270;
  const ex=front?hx:(side?-19:-54),ey=front?hy:-142;
  const mx=front?(sx+ex)/2+25:(side?-49:-72),my=front?Math.min(-176,ey+28):-193;
  const path=`M${sx} ${sy}Q${mx} ${my} ${ex} ${ey}`;
  return <g><path d={path} fill="none" strokeWidth={32}/><path d={path} fill="none" stroke={color} strokeWidth={20}/><path d={`M${ex-9} ${ey-8}q15-15 26 0l-2 19q-19 10-28-4Z`} fill={skin} strokeWidth={5}/>{front&&present>.5&&<path d={`M${ex+8} ${ey-4}l21-18`} fill="none" stroke={skin} strokeWidth={11}/>}</g>;
 };
 return <g data-angle={angle} data-character={family??role} transform={`translate(${x} ${y}) scale(${face==='left'?-s:s} ${s})`} stroke={ink} strokeWidth={8} strokeLinejoin="round" strokeLinecap="round">
  <ellipse cy={8} rx={side?69:85} ry={13} fill={ink} opacity={.16} stroke="none"/>
  <g transform={`rotate(${bow} 0 -140)`}>
   {side?<><path d={`M-16-140L${-28+stride*15} -76L${-9-stride*32} -15M20-140L${43-stride*15} -81L${35+stride*32} -12`} fill="none" strokeWidth={35}/><path d={`M-16-140L${-28+stride*15} -76L${-9-stride*32} -15M20-140L${43-stride*15} -81L${35+stride*32} -12`} fill="none" stroke="#343548" strokeWidth={23}/><path d={`M${-29-stride*32} -19L${9-stride*32} -17L${22-stride*32} 0H${-36-stride*32}ZM${19+stride*32} -18H${53+stride*32}L${73+stride*32} 0H${19+stride*32}Z`} fill="#282436"/></>:<><path d="M-28-142L-35-16M29-143L43-16" fill="none" strokeWidth={36}/><path d="M-28-142L-35-16M29-143L43-16" fill="none" stroke="#343548" strokeWidth={23}/><path d="M-53-22L-16-16L0 0H-59ZM25-22L59-17L78 0H25Z" fill="#282436"/></>}
   {arm(false)}
   <path d={side?'M-32-282Q8-294 34-267L48-138Q6-122-39-139Z':rear?'M-53-280Q0-301 52-280L63-137Q0-116-64-137Z':'M-52-276Q-9-301 42-281L63-139Q2-117-66-137Z'} fill={color}/>
   {rear?<path d="M0-278V-145M-49-227H49" stroke="#242d36" strokeWidth={4}/>:role==='judge'||role==='lawyer'?<path d={side?'M13-280L27-235L36-276L25-262Z':'M-22-281L0-229L25-280L2-263Z'} fill={paper} strokeWidth={4}/>:role==='officer'?<path d="M16-272L36-268L34-257L13-261Z" fill="#afac85" strokeWidth={3}/>:role==='medic'?<path d="M-6-250H8V-236H22V-223H8V-208H-6V-223H-20V-236H-6Z" fill="#47a78f" strokeWidth={3}/>:null}
   <path d={side?'M-7-313V-275Q8-258 27-281V-316':'M-18-315V-276Q0-261 23-280V-314'} fill={skin}/>
   <g transform={`translate(0 -302) rotate(${head} 0 -84)`}>
    {side?<><path d="M-58-174Q-30-211 22-200L55-171L60-130L88-100L68-89L70-43L39-17L-17-24L-49-61Z" fill={skin}/><path d={family==='mother'?'M-52-71Q-83-113-65-168Q-43-213 13-207Q58-201 66-151L43-146L26-171Q5-148-27-141L-27-87Z':'M-57-103L-69-163Q-47-213 16-210L57-181L57-151L27-166L10-145L-34-141L-36-86Z'} fill={hair}/><ellipse cx={-27} cy={-91} rx={15} ry={23} fill={skin}/>{!anonymous&&<><path d="M21-143L54-135" fill="none" strokeWidth={8}/><path d="M17-124Q35-139 57-119L51-87H24Z" fill={paper} strokeWidth={5}/><circle cx={40+gaze*5} cy={-111} r={6} fill={ink} stroke="none"/><path d="M38-48L66-46" fill="none" strokeWidth={5}/></>}{anonymous&&<><path d="M23-106L50-104" fill="none" stroke="#5d6765" strokeWidth={4}/>{mouth>0?<ellipse cx={48} cy={-47} rx={13} ry={8+mouth*4} fill="#282633" strokeWidth={4}/>:<path d="M31-50L56-51" fill="none" stroke="#5d6765" strokeWidth={4}/>}</>}</>:rear?<><path d="M-81-160Q-53-208 12-207Q77-199 88-147L75-47L40-18H-40L-76-48Z" fill={hair}/><path d={family==='mother'?'M-80-52Q-107-111-87-167Q-61-220 5-217Q77-215 92-151Q99-96 75-51L43-26L-35-28Z':'M-83-91L-96-156Q-75-216 4-220Q78-209 92-154L77-84L51-126Q0-151-53-124L-61-75Z'} fill={hair}/><path d="M-32-29H32" fill="none" stroke="#343344" strokeWidth={5}/></>:<><path d="M-84-151Q-64-206 7-207L75-178L96-127L86-44L43-13L-26-22L-77-59Z" fill={skin}/><ellipse cx={-77} cy={-89} rx={17} ry={25} fill={skin}/><path d={family==='mother'?'M-79-65Q-102-108-86-165Q-60-218 6-215Q75-212 91-158L82-114L59-142L39-170Q7-151-48-143L-54-84Z':'M-85-95L-98-158Q-65-219 7-217L78-184L95-136L60-154L43-175L3-154L-51-143L-61-88Z'} fill={hair}/>{anonymous?<path d="M-49-95Q5-109 61-92M-19-47L38-46" fill="none" stroke="#5d6765" strokeWidth={4}/>:<><ellipse cx={-25} cy={-114} rx={28} ry={34} fill={paper} strokeWidth={5}/><ellipse cx={49} cy={-114} rx={23} ry={32} fill={paper} strokeWidth={5}/><circle cx={-15+gaze*7} cy={-111} r={7} fill={ink} stroke="none"/><circle cx={55+gaze*4} cy={-111} r={6} fill={ink} stroke="none"/><path d="M-52-157L-7-164M30-162L72-151" fill="none" strokeWidth={9}/><path d="M20-108L43-67L15-61" fill="#bd7157" strokeWidth={5}/><path d="M-13-30L40-31" fill="none" strokeWidth={6}/></>}</>}
   </g>
   {!hideArm&&arm(true)}
  </g>
 </g>;
};

export const Sheet=({x,y,s=1,angle=0}:{x:number;y:number;s?:number;angle?:number})=><g transform={`translate(${x} ${y}) rotate(${angle}) scale(${s})`} stroke={ink} strokeWidth={5}><path d="M-70-49L57-60L77 40L-64 53Z" fill="#e9e0c9"/><path d="M-45-23L36-31M-42-3L47-11M-39 18L30 11" stroke="#86938c" strokeWidth={4}/></g>;
export const Desk=({x=960,y=820,w=650,side=false}:{x?:number;y?:number;w?:number;side?:boolean})=><g stroke={ink} strokeWidth={7}><path d={`M${x-w/2} ${y}l${side?70:0} -32h${w}l${side?-70:0} 32Z`} fill="#bd8878"/><path d={`M${x-w/2} ${y}h${w}v140h-${w}Z`} fill="#805d60"/><path d={`M${x-w/2+45} ${y+33}h${w-90}v65h-${w-90}Z`} fill="#694f57"/></g>;
export const Flower=({x,y,angle=0,s=1}:{x:number;y:number;angle?:number;s?:number})=><g transform={`translate(${x} ${y}) rotate(${angle}) scale(${s})`} stroke={ink} strokeWidth={3}><path d="M0 0L15 125M8 70Q-32 44-22 97M13 92Q52 61 43 112" fill="#63957c"/>{Array.from({length:8},(_,j)=><ellipse key={j} transform={`rotate(${j*45})`} cy={-17} rx={10} ry={22} fill={paper}/>)}<circle r={10} fill="#c6ca9d"/></g>;

// Maternal identity follows the existing teal employee/parent design and the same role across scenes.
export const Mother=(props:Omit<Props,'role'>)=><AngleActor role="parent" family="mother" {...props}/>;
export const Father=(props:Omit<Props,'role'>)=><AngleActor role="parent" family="father" {...props}/>;

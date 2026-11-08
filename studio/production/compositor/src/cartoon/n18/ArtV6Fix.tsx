import React from 'react';
import {Backdrop,Recruit} from '../n18_v6/Art';
import {AngleActor as Actor,Desk,Sheet,Flower,between as q,ink,paper} from './AngleActors';

const Room=({court=false,reverse=false,memorial=false}:{court?:boolean;reverse?:boolean;memorial?:boolean})=><g stroke={ink} strokeWidth={7}>
 <rect width={1920} height={1080} fill={court?'#625070':memorial?'#a6b7ba':'#b3a8cc'}/>
 <path d={reverse?'M0 60L650 190H1920V790H650L0 1040Z':'M0 160H1270L1920 20V1030L1270 785H0Z'} fill={court?'#44354f':memorial?'#8da4a7':'#9c9db9'}/>
 {(reverse?[180,540,1020,1570]:[170,630,1120,1600]).map(x=><path key={x} d={`M${x} 170v610h46V160Z`} fill={court?'#a28b9e':'#bac6bf'}/>)}
 <path d="M0 812L1920 765V1080H0Z" fill={court?'#7c665d':memorial?'#7e9494':'#817c9c'}/>
 <path d={reverse?'M0 1010L650 810L1920 965':'M0 966L1270 812L1920 1035'} fill="none" stroke={court?'#b49b7f':'#aebbb4'}/>
 {court&&<><path d={reverse?'M1080 670H1860V815H1080Z':'M80 680H860V820H80Z'} fill="#684f59"/><path d={reverse?'M1060 665H1885V696H1060Z':'M60 675H885V706H60Z'} fill="#bd8878"/></>}
 </g>;
const FieldPack=({x,y,books=false,open=false}:{x:number;y:number;books?:boolean;open?:boolean})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={7}><path d="M-87-137Q0-157 88-137L100 85H-100Z" fill="#54746b"/>{books&&[0,1,2,3].map(j=><path key={j} d={`M${-64+j*33} -163h27v94h-27Z`} fill={['#d9c28d','#8596af','#c2c296'][j%3]}/>)}<path d={open?'M-88-135L-99-190L88-182L89-135Z':'M-87-134L-66-90H65L89-133Z'} fill="#81a08a"/><path d="M-61-131V76M62-132V76" stroke="#203f3f" strokeWidth={12}/><path d="M-85-33H85V76H-85Z" fill="#789e87"/></g>;
const BookStack=({x,y,s=1}:{x:number;y:number;s?:number})=><g transform={`translate(${x} ${y}) scale(${s})`} stroke={ink} strokeWidth={5}>{[0,1,2].map(j=><g key={j}><path d={`M-58 ${-12-j*25}h113v23H-58Z`} fill={['#d9c28d','#8596af','#c2c296'][j]}/><path d={`M-42 ${-1-j*25}H44`} stroke="#eee5ca" strokeWidth={6}/></g>)}</g>;
const Chair=({x=650,y=890}:{x?:number;y?:number})=><g stroke={ink} strokeWidth={8}><path d={`M${x-75} ${y-285}h150v168h-150Z`} fill="#b2bdaf"/><path d={`M${x-85} ${y-103}h172v24H${x-85}ZM${x-64} ${y-79}v92M${x+64} ${y-79}v92`} fill="#82918c"/></g>;
const Kit=({x,y,open=0}:{x:number;y:number;open?:number})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={6}><path d={`M-82-23L${-82+open*12} ${-23-open*70}H82V-23Z`} fill="#b4d8c5"/><rect x={-85} y={-22} width={170} height={95} rx={12} fill="#d7e6d8"/><path d="M-11-9H11V11H31V32H11V52H-11V32H-31V11H-11Z" fill="#47a78f" strokeWidth={3}/></g>;
const Gauge=({x,y}:{x:number;y:number})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={6}><path d="M-40-120H38V-10L56 21V55H-55V21L-40-10Z" fill="#d2ebe1"/><path d="M0-99V20" stroke="#db765a" strokeWidth={10}/><circle cy={28} r={20} fill="#db765a"/><path d="M-56 58V140M56 58V140" stroke="#536d6d" strokeWidth={7}/></g>;
const PatientBed=({x=960,y=755}:{x?:number;y?:number})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={7}><path d="M-258-27H252V3H-258ZM-238 4L-215 81M225 4L203 81" fill="#ccded3"/><circle cx={-215} cy={85} r={20} fill="#41495c"/><circle cx={203} cy={85} r={20} fill="#41495c"/><ellipse cx={-180} cy={-75} rx={42} ry={35} fill="#8b9380"/><path d="M-221-82Q-207-132-171-117L-139-87" fill="#697c6f"/><path d="M-134-95Q-23-139 104-83L211-66V-32H-141Z" fill="#adc6ba"/></g>;
const Certificate=({x=1130,y=660}:{x?:number;y?:number})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={6}><path d="M-95-123H95V25H-95Z" fill="#c5cbb8"/><path d="M-78-106H78V7H-78Z" fill="#e5e0c5"/><circle cy={-76} r={13} fill="#b7ae7d"/><path d="M-50-39H50M-39-19H39" stroke="#929b87" strokeWidth={5}/><path d="M-112 33H112L153 88H-150Z" fill="#526969"/></g>;

export const StageV6Fix=({shot:s,f}:{shot:any;f:number})=>{
 const t=f-s.start,p=q(t,0,s.end-s.start),r=q(t,8,42),mode=s.drawing;
 const paperOnDesk=(x:number,y:number)=> <Sheet x={x} y={y} s={.8}/>;
 let scene:React.ReactNode;
 if(mode==='collapse'){
  const fall=q(f,s.fallStart,s.fallEnd),runX=820+(1-fall)*Math.min(100,t*.9);
  scene=<><Backdrop kind="ground" f={0}/><Recruit x={runX} y={840} f={fall>.02?0:t} s={1.05} action={fall>.02?'rest':'run'} fall={fall}/><Actor role="recruit" x={360} y={850} s={.8} angle="rear" head={-q(t,30,66)*8}/><Actor role="officer" x={1510} y={875} s={.82} angle="profile" face="left" head={q(t,38,67)*8}/></>;
 }else if(mode==='ground_wide'){
  scene=<><Backdrop kind="ground" f={0}/>{[0,1,2,3,4,5].map(j=><Actor key={j} role="recruit" x={420+j*230} y={j%2?875:795} s={j%2?.72:.58} angle="rear" head={j===2?r*5:0}/>)}<Actor role="officer" x={200} y={910} s={.92} angle="profile" present={r*.6}/></>;
 }else if(mode==='barracks'){
  scene=<><Backdrop kind="barracks" f={0}/>{[0,1,2,3,4,5].map(j=><Actor key={j} role="recruit" x={300+j*228} y={j%2?900:780} s={j%2?.72:.56} angle={j%2?'profile':'rear'} face={j%2?'left':'right'} head={j===3?-r*12:j===2?r*8:0} present={j===3?.3*(1-r):0}/>)}<Actor role="officer" x={1690-r*90} y={910} s={.98} angle="profile" face="left" present={q(t,42,80)*.75}/></>;
 }else if(mode==='report'||mode==='approve'){
  const reporting=mode==='report';
  scene=<><Room reverse={reporting}/><Actor role="officer" x={reporting?560:1330} y={940} s={1.1} angle="profile" face={reporting?'right':'left'} present={reporting?r*.8:r*.6} head={reporting?0:r*5}/><Actor role="officer" x={reporting?1430:330} y={1010} s={reporting?1.12:1.34} angle="rear" face={reporting?'left':'right'} head={reporting?r*4:0}/><Desk x={960} y={837} w={700} side/>{paperOnDesk(900,798)}</>;
 }else if(mode==='unchecked'){
  scene=<><Backdrop kind="ground" f={0}/><Gauge x={420} y={750}/>{[0,1,2].map(j=><Actor key={j} role="recruit" x={990+j*240} y={860} s={.76} angle="rear"/>)}<Actor role="officer" x={650} y={920} s={1.02} angle="profile" face="right" present={q(t,65,110)*.6} head={-q(t,45,80)*6}/><Sheet x={250} y={798} s={.6}/></>;
 }else if(mode==='order'){
  scene=<><Backdrop kind="ground" f={0}/><Actor role="officer" x={550} y={960} s={1.18} angle="profile" face="right" present={r} head={-r*7}/><Actor role="recruit" x={1510} y={1010} s={1.3} angle="rear" head={r*5}/><Actor role="recruit" x={1150} y={890} s={.87} angle="rear"/></>;
 }else if(mode==='packing_wide'){
  scene=<><Room/>{[0,1,2,3,4,5].map(j=><Actor key={j} role="recruit" x={290+j*260} y={j%2?900:810} s={j%2?.75:.6} angle="rear" head={j===2?r*6:0}/>)}<Desk x={965} y={823} w={490}/><FieldPack x={975} y={750} open/></>;
 }else if(mode==='packing_side'){
  const lift=q(t,20,66),drop=q(t,80,116),handY=-166-lift*71+drop*79;
  scene=<><Room reverse/><g stroke={ink} strokeWidth={7}><path d="M1300 200H1740V780H1300Z" fill="#718d80"/><path d="M1300 390H1740M1300 580H1740"/><path d="M1350 556h85v-83h-85Z" fill="#8e9b88"/></g><Actor role="recruit" x={570} y={940} s={1.08} angle="profile" hand={[65+lift*80+drop*90,handY]} head={8}/><Desk x={1080} y={827} w={780} side/><FieldPack x={1190} y={740} open books={drop>.9}/><g opacity={drop>.9?0:1}><BookStack x={640+lift*120+drop*260} y={755-lift*86+drop*57} s={.9}/></g><Sheet x={885} y={790} s={.55}/></>;
 }else if(mode==='march'||mode==='run'){
  const isRun=mode==='run',base=mode==='march'?f-s.start:t;
  scene=<><Backdrop kind="ground" f={0}/>{[0,1,2,3,4,5].map(j=><Recruit key={j} x={230+j*245+Math.min(165,base*(isRun?1.65:.55))} y={j%2?880:785} f={base} s={j%2?.93:.73} seed={j} action={isRun?'run':'march'} weapon/>)}{isRun&&<Actor role="officer" x={1730} y={906} s={.78} angle="profile" face="left" head={r*4}/>}</>;
 }else if(mode==='race'||mode==='rule_ground'){
  scene=<><Backdrop kind="ground" f={0}/><Actor role="officer" x={480} y={975} s={1.17} angle={mode==='race'?'profile':'rear'} present={mode==='race'?r:0} head={mode==='race'?-r*5:8}/>{[0,1,2].map(j=><Recruit key={j} x={1070+j*220+Math.min(110,t*.9)} y={870-j%2*65} f={mode==='race'?t:0} s={.8-j*.07} action={mode==='race'?'run':'rest'}/>)}</>;
 }else if(mode==='push'){
  scene=<><Backdrop kind="ground" f={0}/>{[0,1,2].map(j=><Recruit key={j} x={520+j*475} y={870-j%2*100} f={t} s={j===1?1:.82} action="push"/>)}<Actor role="officer" x={1730} y={850} s={.73} angle="profile" face="left"/></>;
 }else if(mode==='fallen'||mode==='delay'||mode==='rebuke'||mode==='patient_reverse'){
  const reverse=mode==='patient_reverse',rebuke=mode==='rebuke';
  scene=<><Backdrop kind="ground" f={0}/><Recruit x={reverse?1020:820} y={845} f={0} s={reverse?1.25:1.05} action="rest" fall={1}/><Actor role="recruit" x={reverse?320:430} y={920} s={reverse?1.2:.88} angle={reverse?'rear':'profile'} head={r*12} face="right"/><Actor role="officer" x={1430} y={905} s={1.04} angle="profile" face="left" present={rebuke?r:0} mouth={rebuke?1:0} bow={rebuke?r*9:0} head={rebuke?r*10:10}/>{mode==='fallen'&&<Actor role="recruit" x={1710} y={870} s={.8} angle="rear" head={r*10}/>}</>;
 }else if(mode==='medical_report'){
  scene=<><Room reverse/><Actor role="medic" x={1240} y={945} s={1.17} angle="profile" face="left" head={11-r*7} read={1}/><Desk x={1190} y={827} w={700} side/><Sheet x={1090} y={786} s={.9}/><Kit x={440} y={818}/></>;
 }else if(mode.startsWith('medical')||mode==='loss'){
  const transfer=mode==='medical_transfer',review=mode==='medical_review',results=mode==='medical_results',loss=mode==='loss';
  const dx=transfer?Math.min(220,t*2.3):0;
  scene=<><Backdrop kind="medical" f={0}/>{transfer&&<g stroke={ink} strokeWidth={7}><path d="M160 170H1760V790H160Z" fill={s.location==='sokcho'?'#accabc':'#88a8bd'}/><path d="M640 300H1280V790H640Z" fill="#365466"/><path d="M960 300V790" stroke="#bed3dd" strokeWidth={13}/></g>}<g transform={`translate(${dx} 0)`}><PatientBed x={review?1180:940}/><Actor role="medic" x={review?420:470} y={930} s={1.04} angle={results?'quarter':'profile'} face="right" head={loss?12:review?10-p*9:9} reach={loss?1-r:transfer?.8:.65} hand={transfer?[204,-194]:undefined} stride={transfer&&t<96?Math.sin(t*.28)*.6:0} read={review||results?1:0}/>{!review&&<Actor role="medic" x={1480} y={925} s={1.01} angle="profile" face="left" reach={loss?1-r:.6} hand={transfer?[285,-195]:undefined} stride={transfer&&t<96?-Math.sin(t*.28)*.6:0} head={loss?12:8}/>}</g>{(review||results)&&<><Desk x={review?670:610} y={822} w={330} side/><Sheet x={review?690:620} y={785} angle={p*5} s={.85}/></>}{mode==='medical_care'&&<Kit x={1370} y={850} open={r}/>}</>;
 }else if(mode==='letter'||mode==='record'){
  // This is an anonymous reader of a record, never a re-enacted action by the mother.
  scene=<><Room reverse={mode==='letter'}/><Actor role="reader" x={580} y={930} s={1.13} angle="profile" head={mode==='letter'?11-q(t,123,160)*7:12} hand={[100+q(t,25,105)*55,-148]} read={1}/><Desk x={1060} y={830} w={850} side/><Sheet x={925} y={780} s={1.15} angle={-6}/>{mode==='letter'&&<g transform="translate(1360 771) rotate(-12)" stroke={ink} strokeWidth={6}><path d="M-55-43H55V26H-55Z" fill="#304657"/><path d="M-48-47Q-65-56-72-33L-44 38Q-32 52-16 40L-7 24L-31 2L-43 8L-56-19L-39-24Z" fill="#253746"/><path d="M-6-18H32M-4-3H34" stroke="#779e9e" strokeWidth={4}/></g>}</>;
 }else if(mode.startsWith('court')||mode.startsWith('appeal')||mode==='supreme_wide'){
  const wide=/wide/.test(mode),defendants=/defendants|reaction/.test(mode),counsel=/counsel|prosecutor|files/.test(mode),deputy=mode==='court_deputy',commander=mode==='court_commander';
  if(wide){
   scene=<><Backdrop kind="court" f={0}/><Actor role="judge" x={1460} y={800} s={.83} angle="quarter" face="left" head={10-r*10} read={1-r*.4} present={r*.4}/><Desk x={1460} y={760} w={410}/>{paperOnDesk(1340,718)}<Actor role="lawyer" x={380} y={900} s={.88} angle="profile" head={6} present={mode==='court_indict_wide'?r*.7:0}/><Desk x={380} y={830} w={330}/><Actor role="commander" x={760} y={930} s={.79} angle="rear" head={r*4}/><Actor role="deputy" x={990} y={930} s={.76} angle="rear" head={r*4}/></>;
  }else if(mode==='court_witness_wide'){
   scene=null;
  }else if(defendants||deputy||commander){
   const two=defendants;
   scene=<><Room court reverse/><Actor role={deputy?'deputy':'commander'} x={two?800:1000} y={970} s={1.12} angle={deputy?'profile':'quarter'} face="right" head={r*(mode==='court_reaction'?10:5)} read={0}/>{two&&<Actor role="deputy" x={1330} y={955} s={1.04} angle="profile" head={r*8}/>}<path d="M480 888H1620V938H480Z" stroke={ink} strokeWidth={8} fill="#805d60"/><Actor role="lawyer" x={220} y={1110} s={1.4} angle="rear"/></>;
  }else if(counsel){
   const files=/files/.test(mode),request=/prosecutor/.test(mode);
   scene=<><Room court reverse/><Actor role="lawyer" x={570} y={955} s={1.16} angle="profile" head={files?10:4-r*4} present={files?0:r*.9} hand={files?[80+p*90,-150]:undefined} read={files?1:0}/><Desk x={files?1010:700} y={830} w={files?760:500} side/>{files?[0,1,2,3,4,5].map(j=><Sheet key={j} x={825+j*73+(j<3?-1:1)*q(t,10,100)*22} y={785+(j%2)*9} s={.43} angle={j*4-10}/>):paperOnDesk(775,789)}<Actor role={request?'deputy':'commander'} x={1590} y={1030} s={1.35} angle="rear" head={r*5}/></>;
  }else if(mode==='court_records'){
   scene=<><Room court/><Actor role="reader" x={570} y={945} s={1.1} angle="profile" read={1} head={10}/><Desk x={1020} y={832} w={820} side/><Sheet x={870-q(t,15,65)*42} y={790} s={.75}/><Sheet x={1190+q(t,80,130)*40} y={790} s={.75}/></>;
  }else{
   const turning=mode==='court_page',distinguish=mode==='court_distinguish';
   scene=<><Room court/><Actor role="judge" x={1240} y={945} s={1.17} angle={mode==='court_judge_reverse'?'quarter':'profile'} face="left" head={turning?9:10-r*10} gaze={r} present={distinguish?r*.5:0} read={turning?1:1-r*.3} hand={turning?[80+r*55,-180-r*35]:undefined}/><Desk x={1190} y={826} w={720} side/><Sheet x={1080} y={787} s={.9} angle={turning?-q(t,5,52)*13:0}/>{distinguish&&<Sheet x={1370} y={787} s={.8}/>}<Actor role="commander" x={250} y={1090} s={1.52} angle="rear" head={r*3}/></>;
  }
 }else if(mode==='witness_wide'||mode==='witness_books'||mode==='witness_reaction'){
  const wide=mode==='witness_wide',books=mode==='witness_books';
  scene=<><Backdrop kind="court" f={0}/>{wide?[0,1,2,3].map(j=><Actor key={j} role="recruit" x={530+j*285} y={930} s={j===1?.98:.76} angle={j===1?'profile':'rear'} head={j===1?8-r*8:0} present={j===1?r*.5:0}/>):<><Actor role="recruit" x={850} y={945} s={1.23} angle="profile" head={books?8:r*14-q(t,100,170)*6} present={books?r*.5:0}/><Actor role="judge" x={1520} y={790} s={.67} angle="profile" face="left" head={6}/></>}<Desk x={wide?815:875} y={854} w={wide?360:450}/>{books&&<FieldPack x={1270} y={820} books/>}</>;
 }else if(mode==='prosecution'){
  scene=<><Room/><Actor role="lawyer" x={600} y={945} s={1.15} angle="profile" read={1} head={11-p*6} hand={[100+p*50,-150]}/><Desk x={1080} y={832} w={850} side/>{[0,1,2].map(j=><Sheet key={j} x={845+j*185} y={785+j%2*7} s={.75} angle={-8+j*6}/>)}</>;
 }else if(mode==='policy_wide'||mode==='policy_speaker'||mode==='policy_calendar'){
  const wide=mode==='policy_wide',cal=mode==='policy_calendar';
  scene=<><Room reverse={wide}/><Actor role="officer" x={wide?1140:1000} y={935} s={wide?1.0:1.17} angle={wide?'quarter':'profile'} face="left" head={cal?10:6-r*6} read={cal?1:.55} present={cal?0:r*.8}/><Desk x={wide?1130:950} y={835} w={wide?400:620} side/><Sheet x={wide?1090:980} y={793} s={.8} angle={cal?-r*10:0}/>{wide&&<><Actor role="reader" x={330} y={1020} s={1.2} angle="rear" head={r*3}/><Actor role="officer" x={1680} y={1010} s={1.15} angle="rear"/></>}</>;
 }else if(mode==='policy_listen'||mode==='policy_authorize'){
  const authorize=mode==='policy_authorize';
  scene=<><Room reverse={authorize}/><Actor role={authorize?'officer':'recruit'} x={580} y={940} s={1.08} angle="profile" present={authorize?0:r*.65} head={6}/><Actor role="officer" x={1390} y={940} s={1.11} angle="profile" face="left" head={q(t,15,65)*6} hand={authorize?[65+q(t,40,90)*65,-155-q(t,40,90)*30]:undefined} read={authorize?1:0}/><Desk x={1020} y={830} w={620} side/><Sheet x={1100} y={789} s={.75}/></>;
 }else if(mode==='policy_checks'){
  // Announced procedure, shown as a conceptual demonstration, not evidence of implementation.
  const health=q(t,0,42),weather=q(t,43,82),kit=q(t,83,138);
  scene=<><Backdrop kind="ground" f={0}/><Actor role="recruit" x={560} y={920} s={1.01} angle="profile" head={health*5}/><Actor role="officer" x={850} y={920} s={1.01} angle={t<43||t>=160&&t<183?'profile':t<58||t>=183&&t<196?'rear':'profile'} face={t<43||t>=160&&t<183?'left':'right'} head={t<43||t>=160&&t<183?health*7:9} read={health*.4} present={health*.35}/><Gauge x={1130} y={770}/><Actor role="medic" x={1500} y={920} s={1.0} angle="profile" face="left" head={kit*12} hand={[45+kit*60,-140-kit*20]}/><Kit x={1320} y={805} open={kit}/></>;
 }else if(mode==='policy_measure'){
  scene=<><Backdrop kind="ground" f={0}/><Actor role="officer" x={680} y={950} s={1.16} angle="profile" head={8+r*3} hand={[80+r*30,-164]}/><Gauge x={1070} y={719}/><Actor role="recruit" x={1510} y={895} s={.85} angle="rear"/><Desk x={800} y={840} w={260}/><Sheet x={820} y={805} s={.65}/></>;
 }else if(mode==='policy_field'){
  scene=<><Backdrop kind="ground" f={0}/><Actor role="officer" x={520} y={930} s={1.1} angle="profile" head={11-r*12} read={1-r*.6}/><Sheet x={580.2+r*18.48} y={678.1+r*54.12} s={.75} angle={-8}/><Actor role="recruit" x={1350} y={900} s={.94} angle="rear"/><Gauge x={1650} y={760}/></>;
 }else if(mode==='memorial_wide'||mode==='memorial_letter'||mode==='memorial_flowers'){
  const flowers=mode==='memorial_flowers',letter=mode==='memorial_letter';
  const place=q(t,12,55),withdraw=q(t,60,82);
  scene=<><Room memorial reverse={flowers}/><Chair x={690} y={870}/><path d="M1030 695H1580V855H1030Z" fill="#43535f" stroke={ink} strokeWidth={7}/><Certificate x={1270} y={655}/>{[0,1,2,3,4].map(j=><Flower key={j} x={1090+j*100} y={731} s={.8}/>)}<Actor role={letter?'reader':'visitor'} x={flowers?760:360} y={950} s={flowers?1.1:1.12} angle={flowers||letter?'profile':'rear'} head={flowers?place*11:letter?12:7} read={letter?1:0} bow={flowers?place*9:0} hand={flowers?[70+place*105-withdraw*50,-151+place*17]:letter?[80,-160]:undefined}/>{flowers&&<Flower x={837+place*180} y={774-place*14} angle={place*72} s={.83}/>}<Actor role="visitor" x={1730} y={925} s={.9} angle="rear" head={7}/>{letter&&<><Desk x={380} y={860} w={300}/><Sheet x={400} y={815} s={.8}/></>}</>;
 }else if(mode==='farewell'){
  const touch=q(t,8,42),pat=q(t,55,75)-q(t,78,100);
  scene=<><Backdrop kind="ground" f={0}/><Actor role="parent" x={530} y={925} s={1.0} angle="profile" hideArm head={4}/><Actor role="parent" x={1330} y={925} s={1.0} angle="rear" head={4}/><Actor role="recruit" x={930} y={925} s={1.03} angle="profile" hideArm head={touch*5}/><g stroke={ink} strokeWidth={29} strokeLinecap="round" fill="none"><path d={`M900 665Q790 695 ${710-touch*50} 720M963 675Q1090 ${670-pat*20} 1280 ${710-pat*20}M570 665Q615 715 ${660} 720`}/></g><g strokeWidth={18} strokeLinecap="round" fill="none"><path d={`M900 665Q790 695 ${710-touch*50} 720M963 675Q1090 ${670-pat*20} 1280 ${710-pat*20}`} stroke="#648257"/><path d="M570 665Q615 715 660 720" stroke="#56a698"/></g><ellipse cx={660} cy={720} rx={20} ry={15} fill="#797f79" stroke={ink} strokeWidth={5}/></>;
 }else if(mode==='yongsan'||mode==='closing'){
  const arriving=mode==='yongsan',approach=arriving?q(t,0,54):1,bow=arriving?q(t,66,93):1;
  scene=<><Room memorial/><path d="M780 320H1260V790H780Z" fill="#34414c" stroke={ink} strokeWidth={8}/><path d="M865 460L1030 625L1115 510M951 444L1099 590" fill="none" stroke="#aaaeb0" strokeWidth={24}/><path d="M645 770H1400V851H645Z" fill="#526969" stroke={ink} strokeWidth={8}/>{[0,1,2,3,4,5].map(j=><Flower key={j} x={740+j*110} y={760} s={.85}/>)}<Actor role="parent" x={420} y={950} s={1.08} angle="rear" head={arriving?bow*8:8}/><Actor role="parent" x={1510} y={950} s={1.05} angle="rear" head={arriving?bow*8:8}/><Actor role="visitor" x={1630-approach*390} y={980} s={.94} angle="profile" face="left" stride={arriving&&t<54?Math.sin(t*.25)*Math.sin(Math.PI*t/54):0} bow={bow*17} head={bow*8}/></>;
 }else scene=<Backdrop kind="ground" f={0}/>;
 return <g data-shot={s.id} data-drawing={mode}>{scene}<path d="M0 926H1920V1080H0Z" fill={ink}/></g>;
};

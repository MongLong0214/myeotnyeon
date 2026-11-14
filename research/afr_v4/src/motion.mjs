export const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v));
export const mix=(a,b,u)=>a+(b-a)*u;
export const ease=u=>{u=clamp(u);return u*u*(3-2*u);};
export const beat=(t,a,b)=>ease((t-a)/(b-a));
export const held=(t,fps=24)=>Math.floor(t*fps/2+1e-7)*2/fps;
export function blink(t,offset=0){
 const v=((t+offset)%3.7+3.7)%3.7;
 return v<.08?1-v/.08:v<.17?(v-.08)/.09:1;
}
export function stepPose(t,a,b,x0,x1){
 const u=clamp((t-a)/(b-a));
 const foot=(phase)=>({x:mix(x0,x1,ease(phase)),lift:Math.sin(Math.PI*clamp(phase))*.12});
 return {x:mix(x0,x1,ease(u)),left:foot(u*2),right:foot(u*2-1),active:u>0&&u<1};
}
// Analytic two-bone solution. Unsupported reach is explicit, never silently stretching a limb.
export function elbowFor(shoulder,hand,a,b,hint){
 const d=hand.clone().sub(shoulder),len=d.length();
 if(len>a+b+1e-4||len<Math.abs(a-b)+1e-4)throw new Error('Hand target outside this actor rig reach');
 const axis=d.clone().normalize();
 const along=(a*a-b*b+len*len)/(2*len);
 const side=hint.clone().sub(shoulder);side.addScaledVector(axis,-side.dot(axis));
 if(side.length()<1e-6)side.set(0,0,1).addScaledVector(axis,-axis.z);
 return shoulder.clone().addScaledVector(axis,along).addScaledVector(side.normalize(),Math.sqrt(Math.max(0,a*a-along*along)));
}

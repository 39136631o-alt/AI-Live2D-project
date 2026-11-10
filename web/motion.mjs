/** Frame-rate independent motion primitives; no DOM or runtime dependencies. */
export const clamp = (v,lo,hi)=>Math.max(lo,Math.min(hi,v));
export const smoothstep = x=>{x=clamp(x,0,1);return x*x*(3-2*x);};
export const damp = (current,target,rate,dt)=>target+(current-target)*Math.exp(-rate*dt);
export function envelope(elapsed,duration=2.4) {
  if(elapsed<0||elapsed>=duration) return 0;
  return smoothstep(elapsed/.35)*smoothstep((duration-elapsed)/.5);
}
export function blinkAt(t) {
  // Repeatable varied intervals; quick closure, slower reopening; occasional double blink.
  const phase=((t%13.9)+13.9)%13.9;
  let open=1;
  for(const center of [1.34,5.82,10.62,10.96]) {
    const delta=phase-center;
    if(delta>=-.14&&delta<=0) open=Math.min(open,1-smoothstep((delta+.14)/.14));
    if(delta>0&&delta<.22) open=Math.min(open,smoothstep(delta/.22));
  }
  return open;
}
export function spring(state,target,dt,stiffness=30,damping=10) {
  // Substeps bound integration error even after a slow frame; never integrate hidden time.
  const n=Math.max(1,Math.ceil(clamp(dt,0,.05)/(.008333333)));
  const h=clamp(dt,0,.05)/n;
  for(let i=0;i<n;i++) {state.velocity+=((target-state.value)*stiffness-state.velocity*damping)*h;state.value+=state.velocity*h;}
  return state.value;
}
export class FrameMeter {
  constructor(){this.reset();}
  reset(){this.last=null;this.elapsed=0;this.frames=0;this.fps=null;}
  sample(stamp) {
    if(this.last!==null) {
      const dt=stamp-this.last;
      if(dt>0&&dt<1000){this.elapsed+=dt;this.frames++;}
    }
    this.last=stamp;
    if(this.elapsed>=750){this.fps=this.frames*1000/this.elapsed;this.frames=0;this.elapsed=0;return this.fps;}
    return null;
  }
}

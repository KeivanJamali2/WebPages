import { sounds } from './sounds.js';

// Toast notification system
const toastStack = document.createElement('div');
toastStack.className = 'toast-stack';
window.addEventListener('DOMContentLoaded', ()=> document.body.appendChild(toastStack));

export function toast(msg, opts={}){
  const { tone='neutral', life=3500 } = opts;
  const el = document.createElement('div');
  el.className = 'toast ' + (tone==='good'?'good': tone==='warn'?'warn': tone==='bad'?'bad':'');
  el.textContent = msg;
  toastStack.appendChild(el);
  setTimeout(()=>{
    el.style.animation = 'toast-out .6s forwards';
    el.addEventListener('animationend', ()=> el.remove());
  }, life);
}

// Small helper for state diffs
export function diffStates(prev, next){
  if(!prev) return { changes:['init'] };
  const changes = [];
  if(prev.status !== next.status) changes.push('status:' + prev.status + '>' + next.status);
  if(prev.round !== next.round) changes.push('round');
  if(prev.prompt !== next.prompt) changes.push('prompt');
  if(prev.submitted_count !== next.submitted_count) changes.push('submitted');
  if(prev.decided_count !== next.decided_count) changes.push('decided');
  return { changes };
}

export function animatePulse(el){
  el.animate([
    { transform:'scale(1)', filter:'brightness(1)' },
    { transform:'scale(1.04)', filter:'brightness(1.25)' },
    { transform:'scale(1)', filter:'brightness(1)' }
  ], { duration:650, easing:'cubic-bezier(.6,.2,.1,1)'});
}

export function listTransition(container){
  const children = Array.from(container.children);
  children.forEach((c,i)=>{
    c.style.opacity=0; c.style.transform='translateY(6px)';
    requestAnimationFrame(()=>{
      c.style.transition='all .55s cubic-bezier(.55,.2,.2,1)';
      c.style.opacity=1; c.style.transform='translateY(0)'; c.style.transitionDelay = (i*40)+'ms';
    });
  });
}

// Play context aware sound cues
export function handleSounds(prev, next){
  if(!prev){ return; }
  if(prev.prompt !== next.prompt) sounds.play('prompt');
  // on submission change (increase submitted_count)
  if(next.submitted_count > prev.submitted_count) sounds.play('submit');
  if(next.decided_count > prev.decided_count){
    // check which new decision(s) added
    const prevMap = new Map(prev.players.map(p=>[p.name,p.decision]));
    next.players.forEach(p=>{
      if(p.decision && prevMap.get(p.name) !== p.decision){
        if(p.decision === 'same') sounds.play('same'); else sounds.play('again');
      }
    });
  }
  if(prev.status !== 'finished' && next.status === 'finished') sounds.play('same');
}

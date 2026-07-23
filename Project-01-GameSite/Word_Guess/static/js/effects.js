/* Effects & Audio Manager for Word Guess Game
 * Provides:
 *  - SoundManager: preloads short UI sounds (beep, success, fail, click, reveal)
 *  - Confetti: lightweight canvas-less particle system using DOM for win events
 *  - Utility animation helpers (pulse / flash)
 *  - Graceful degradation + reduced-motion preference detection
 */
// Enhanced Effects & Audio Manager
// - Adds celebration modes: none | subtle | full
// - Subtle mode uses fewer particles & shorter lifespan
// - Full mode similar to previous (slightly optimized)
// - Respects user reduced-motion and a data attribute on #confetti-layer
// - Provides safe lazy audio unlock on first user interaction
(function(global){
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const layer = document.getElementById('confetti-layer');
  let celebrationMode = 'full';
  if(layer){
    celebrationMode = (layer.getAttribute('data-celebration-mode') || 'full').toLowerCase();
    if(['none','off','false'].includes(celebrationMode)) celebrationMode = 'none';
    if(!['none','subtle','full'].includes(celebrationMode)) celebrationMode = 'full';
  }

  /* ------------------------------- Sound Manager ------------------------------- */
  class SoundManager {
    constructor(){
      this.enabled = true;
      this.ctx = null;
      this.buffers = new Map();
      this.initialized = false;
    }
    ensureContext(){
      if(!this.ctx){
        const AC = window.AudioContext || window.webkitAudioContext;
        if(AC) this.ctx = new AC();
      }
      // On some mobile browsers need a resume after user gesture
      if(this.ctx && this.ctx.state === 'suspended'){
        this.ctx.resume().catch(()=>{});
      }
    }
    toggle(on){
      this.enabled = on;
    }
    async init(){
      if(this.initialized) return;
      this.ensureContext();
      this.initialized = true;
      // Generate a few procedural buffers
      this.buffers.set('beep', this._makeBeep(660,0.18));
      this.buffers.set('click', this._makeBeep(300,0.08));
      this.buffers.set('success', this._makeChord([880,1320],0.35));
      this.buffers.set('fail', this._makeNoise(0.35));
      this.buffers.set('reveal', this._makeSweep());
    }
    play(name, opts={}){
      if(!this.enabled) return;
      this.init();
      const buf = this.buffers.get(name);
      if(!buf || !this.ctx) return;
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      const gain = this.ctx.createGain();
      gain.gain.value = (opts.volume ?? 1) * 0.55;
      src.connect(gain).connect(this.ctx.destination);
      if(opts.playbackRate) src.playbackRate.value = opts.playbackRate;
      try { src.start(); } catch(_){}
    }
    _makeBeep(freq, dur){
      if(!this.ctx) return null;
      const sr = this.ctx.sampleRate;
      const len = Math.floor(sr * dur);
      const buf = this.ctx.createBuffer(1, len, sr);
      const data = buf.getChannelData(0);
      for(let i=0;i<len;i++){
        const t = i / sr;
        data[i] = Math.sin(2*Math.PI*freq*t) * Math.exp(-3*t);
      }
      return buf;
    }
    _makeChord(freqs,dur){
      if(!this.ctx) return null;
      const sr = this.ctx.sampleRate; const len = Math.floor(sr*dur);
      const buf = this.ctx.createBuffer(1,len,sr); const d=buf.getChannelData(0);
      for(let i=0;i<len;i++){
        const t=i/sr; let v=0; freqs.forEach(f=> v += Math.sin(2*Math.PI*f*t));
        d[i]=(v/freqs.length)*Math.exp(-3*t);
      }
      return buf;
    }
    _makeNoise(dur){
      if(!this.ctx) return null;
      const sr=this.ctx.sampleRate; const len=Math.floor(sr*dur);
      const buf=this.ctx.createBuffer(1,len,sr); const d=buf.getChannelData(0);
      for(let i=0;i<len;i++){
        const t=i/sr; d[i]=(Math.random()*2-1)*Math.exp(-5*t);
      }
      return buf;
    }
    _makeSweep(){
      if(!this.ctx) return null;
      const sr=this.ctx.sampleRate; const dur=0.8; const len=Math.floor(sr*dur);
      const buf=this.ctx.createBuffer(1,len,sr); const d=buf.getChannelData(0);
      const start=300, end=1400;
      for(let i=0;i<len;i++){
        const t=i/sr; const f=start + (end-start)*Math.pow(t,0.6);
        d[i]=Math.sin(2*Math.PI*f*t) * Math.exp(-2*t);
      }
      return buf;
    }
  }

  const sounds = new SoundManager();
  global.WGSounds = sounds;

  /* -------------------------------- Confetti FX -------------------------------- */
  function launchConfetti(opts={}){
    if(!layer || prefersReduced || celebrationMode==='none') return;
    const mode = celebrationMode === 'subtle' ? 'subtle' : (opts.mode || celebrationMode);
    const baseCount = mode==='subtle' ? 18 : 42;
    const count = opts.count || baseCount;
    // Use a DocumentFragment for reduced layout thrash
    const frag = document.createDocumentFragment();
    for(let i=0;i<count;i++){
      const el = document.createElement('div');
      el.className='confetti-piece';
      const hue = Math.round(30 + Math.random()*70);
      const sat = 70 + Math.random()*25;
      const lit = 50 + Math.random()*15;
      el.style.setProperty('--h', hue);
      el.style.setProperty('--s', sat);
      el.style.setProperty('--l', lit);
      const size = (mode==='subtle'?4:6) + Math.random()*(mode==='subtle'?6:10);
      el.style.width = el.style.height = size+'px';
      el.style.left = (Math.random()*100)+'%';
      const fall = (mode==='subtle'?2400:3400) + Math.random()*(mode==='subtle'?1200:2400);
      const drift = (Math.random()*2-1) * (mode==='subtle'?60:120);
      const rotate = (Math.random()*720 - 360);
      // Stagger start for smoother feel
      const delay = Math.random()* (mode==='subtle'?150:300);
      requestAnimationFrame(()=>{
        el.animate([
          { transform:`translate3d(0,-14px,0) rotateZ(0deg)`, opacity:0},
          { transform:`translate3d(${drift/2}px,40vh,0) rotateZ(${rotate/2}deg)`, opacity:1},
          { transform:`translate3d(${drift}px,100vh,0) rotateZ(${rotate}deg)`, opacity:0}
        ], { duration: fall, easing:'cubic-bezier(.25,.6,.35,1.0)', fill:'forwards', delay });
      });
      frag.appendChild(el);
      setTimeout(()=> el.remove(), fall + delay + 200);
    }
    layer.appendChild(frag);
  }
  global.WGConfetti = { launch: launchConfetti };

  /* ------------------------------ Utility Animations --------------------------- */
  function pulse(el){ if(!el) return; el.animate([{transform:'scale(1)'},{transform:'scale(1.06)'},{transform:'scale(1)'}],{duration:400,easing:'ease-out'}); }
  function flash(el){ if(!el) return; el.animate([{backgroundColor:'rgba(255,255,255,0)'},{backgroundColor:'rgba(255,255,255,0.15)'},{backgroundColor:'rgba(255,255,255,0)'}],{duration:600,easing:'ease'}); }
  global.WGFx = { pulse, flash };

  // Accessibility: allow dynamic update of celebration mode later
  global.WGSetCelebrationMode = function(mode){
    celebrationMode = (mode||'full').toLowerCase();
    if(['none','off','false'].includes(celebrationMode)) celebrationMode='none';
    if(!['none','subtle','full'].includes(celebrationMode)) celebrationMode='full';
  };

  // Lazy unlock audio after first interaction (mobile autoplay policies)
  function unlockAudio(){
    if(!global.WGSounds) return;
    try { global.WGSounds.ensureContext(); } catch(_){ }
    ['click','touchstart','keydown'].forEach(evt=> document.removeEventListener(evt, unlockAudio, true));
  }
  ['click','touchstart','keydown'].forEach(evt=> document.addEventListener(evt, unlockAudio, true));

})(window);

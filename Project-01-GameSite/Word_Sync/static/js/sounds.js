// Sound & haptic feedback system using Web Audio API + small synthesized buffers
// We synthesize short tones procedurally to avoid bundling large audio files.

class Soundscape {
  constructor(){
    this.ctx = null;
    this.buffers = {};
    this.enabled = true;
  }
  _ctx(){ if(!this.ctx){ this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } return this.ctx; }
  async resume(){ if(this.ctx && this.ctx.state === 'suspended'){ await this.ctx.resume(); } }
  createTone({freq=440, duration=.25, type='sine', attack=0.01, release=0.08, detune=0, gain=.25, bend=0}={}){
    const ctx = this._ctx();
    const sampleRate = ctx.sampleRate;
    const length = Math.floor(duration * sampleRate);
    const data = new Float32Array(length);
    for(let i=0;i<length;i++){
      const t = i / sampleRate;
      const envA = Math.min(1, t/attack);
      const envR = Math.min(1, (duration - t)/release);
      const env = Math.min(envA, envR);
      const f = freq * Math.pow(2, bend * t);
      let v;
      switch(type){
        case 'square': v = Math.sign(Math.sin(2*Math.PI*f*t)); break;
        case 'saw': v = 2*(t*f - Math.floor(.5 + t*f)); break;
        case 'triangle': v = Math.asin(Math.sin(2*Math.PI*f*t))*2/Math.PI; break;
        default: v = Math.sin(2*Math.PI*f*t);
      }
      const det = detune? Math.sin(2*Math.PI*(f+detune)*t)*.5 : 0;
      data[i] = (v*.8 + det*.2) * env * gain;
    }
    const buffer = ctx.createBuffer(1, length, sampleRate);
    buffer.copyToChannel(data,0,0);
    return buffer;
  }
  loadPreset(name, chain){
    const bufs = chain.map(cfg=> this.createTone(cfg));
    this.buffers[name] = bufs;
  }
  play(name){
    if(!this.enabled) return;
    const ctx = this._ctx();
    const bufs = this.buffers[name];
    if(!bufs) return;
    const now = ctx.currentTime;
    bufs.forEach((b,i)=>{
      const src = ctx.createBufferSource();
      src.buffer = b;
      const gain = ctx.createGain();
      gain.gain.value = 1;
      src.connect(gain).connect(ctx.destination);
      src.start(now + i*0.01);
    });
  }
  toggle(flag){ this.enabled = flag; }
}

export const sounds = new Soundscape();
// Preset design: short tactile melodic cues.
// submit: ascending shimmer; same: chord; again: soft pulse downward; prompt change: airy blip; reset: sparkling sweep

function initSounds(){
  sounds.loadPreset('submit', [
    {freq:420, duration:.16, type:'sine', gain:.35},
    {freq:630, duration:.22, type:'sine', gain:.25},
    {freq:880, duration:.28, type:'triangle', gain:.18}
  ]);
  sounds.loadPreset('same', [
    {freq:330, duration:.34, type:'triangle', gain:.28},
    {freq:495, duration:.42, type:'sine', gain:.22},
    {freq:660, duration:.5, type:'sine', gain:.16}
  ]);
  sounds.loadPreset('again', [
    {freq:620, duration:.24, type:'saw', bend:-0.6, gain:.18},
    {freq:440, duration:.32, type:'triangle', gain:.22},
    {freq:296, duration:.42, type:'sine', gain:.18}
  ]);
  sounds.loadPreset('prompt', [
    {freq:512, duration:.18, type:'sine', gain:.25},
    {freq:768, duration:.30, type:'sine', gain:.18}
  ]);
  sounds.loadPreset('reset', [
    {freq:260, duration:.18, type:'triangle', gain:.22},
    {freq:390, duration:.26, type:'triangle', gain:.20},
    {freq:520, duration:.34, type:'sine', gain:.18},
    {freq:780, duration:.40, type:'sine', gain:.14}
  ]);
  // very short notification blip for incoming chat
  sounds.loadPreset('chat', [
    {freq:1040, duration:.085, type:'sine', gain:.28},
    {freq:1560, duration:.11, type:'sine', gain:.18}
  ]);
}

initSounds();

// Fallback unlocking on first interaction
window.addEventListener('pointerdown', ()=> sounds.resume(), {once:true});

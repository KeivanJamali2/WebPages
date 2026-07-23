// Cozy Fantasy Background: floating embers + subtle parallax
// Honors prefers-reduced-motion. Lightweight (no heavy canvas draws on idle).
(function(){
  const canvas = document.getElementById('bg-embers');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let w = canvas.width = window.innerWidth;
  let h = canvas.height = window.innerHeight;
  const DPR = window.devicePixelRatio || 1;
  canvas.width = w * DPR; canvas.height = h * DPR; canvas.style.width = w+'px'; canvas.style.height = h+'px'; ctx.scale(DPR,DPR);

  const emberCount = prefersReduced ? 18 : 55;
  const embers = [];
  function spawn(){
    for(let i=0;i<emberCount;i++){
      embers.push({
        x: Math.random()*w,
        y: h + Math.random()*h*0.4,
        r: 1 + Math.random()*2.2,
        vy: 0.25 + Math.random()*0.55,
        drift: (Math.random()*0.4 - 0.2),
        hue: 28 + Math.random()*25,
        life: 0,
        maxLife: 4000 + Math.random()*4000
      });
    }
  }
  spawn();

  let last = performance.now();
  function tick(now){
    const dt = now - last; last = now;
    if(!ctx) return;
    ctx.clearRect(0,0,w,h);
    for(const e of embers){
      e.y -= e.vy * (dt/16);
      e.x += e.drift * (dt/16);
      e.life += dt;
      if(e.y < -20 || e.life > e.maxLife){
        e.x = Math.random()*w; e.y = h + Math.random()*60; e.life = 0; e.maxLife = 4000 + Math.random()*4000;
      }
      const alpha = 1 - (e.life / e.maxLife);
      const grd = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r*4);
      grd.addColorStop(0, `hsla(${e.hue}deg 100% 65% / ${0.55*alpha})`);
      grd.addColorStop(1, 'hsla(30deg 30% 10% / 0)');
      ctx.fillStyle = grd;
      ctx.beginPath(); ctx.arc(e.x,e.y,e.r*4,0,Math.PI*2); ctx.fill();
    }
    if(!prefersReduced) requestAnimationFrame(tick);
  }
  if(!prefersReduced) requestAnimationFrame(tick);

  // Resize handling
  window.addEventListener('resize', ()=>{
    w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight;
    canvas.width = w * DPR; canvas.height = h * DPR; canvas.style.width = w+'px'; canvas.style.height = h+'px'; ctx.scale(DPR,DPR);
  });

  // Parallax on pointer move
  const mist = document.getElementById('parallax-mist');
  if(mist && !prefersReduced){
    window.addEventListener('pointermove', (e)=>{
      const x = (e.clientX / w - 0.5) * 12;
      const y = (e.clientY / h - 0.5) * 12;
      mist.style.transform = `translate(${x}px, ${y}px)`;
    });
  }
})();

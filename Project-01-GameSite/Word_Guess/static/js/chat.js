(function(){
  const layout = document.querySelector('.chat-layout');
  if(!layout) return;
  const roomId = layout.getAttribute('data-room-id');
  const logEl = document.getElementById('chat-log');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const readyBtn = document.getElementById('ready-btn');
  const botBtn = document.getElementById('bot-btn');
  const bigTimer = document.getElementById('chat-timer-big');
  const miniTimer = document.getElementById('mini-timer');
  const readyIndicator = document.getElementById('ready-indicator');
  const personaTag = document.getElementById('persona-tag');
  const personalQ = document.getElementById('personal-questions');
  const personalG = document.getElementById('personal-guesses');

  let chatDeadline = null; // epoch seconds (during chat or postgame cooldown)
  let phase = 'CHAT'; // or COMPLETED for postgame chat window
  let timerInt = null;

  function play(kind='click'){
    if(window.WGSounds){ window.WGSounds.play(kind); return; }
  }

  function fmt(sec){ if(!sec && sec!==0) return '--:--'; let s=Math.max(0,Math.floor(sec)); const m=Math.floor(s/60); s=s%60; return `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`; }

  function tickTimers(){
    if(!chatDeadline){ if(bigTimer) bigTimer.textContent='--:--'; if(miniTimer) miniTimer.textContent='--:--'; return; }
    const left = chatDeadline - Date.now()/1000;
    const txt = fmt(left);
    if(bigTimer) bigTimer.textContent = txt;
    if(miniTimer) miniTimer.textContent = txt;
    if(left <= 0){ clearInterval(timerInt); timerInt=null; }
  }

  function ensureTimer(){ if(timerInt) return; timerInt = setInterval(tickTimers, 1000); tickTimers(); }

  function addChat(entry){
    if(!logEl) return; const li=document.createElement('li');
    const dt = new Date(entry.ts*1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    li.innerHTML = `<span class="who">${entry.player}</span><span class="msg">${entry.msg}</span><span class="ts">${dt}</span>`;
    logEl.appendChild(li); logEl.scrollTop = logEl.scrollHeight; }

  function renderState(state){
    if(!state || !state.game) return;
    const g = state.game;
    // Permit staying here if either in CHAT phase or postgame cooldown window
    const inPostgame = g.is_over && state.postgame_deadline;
    if(g.phase && g.phase !== 'CHAT' && !inPostgame){
      // phase advanced out of chat & not in postgame -> return to room
      window.location.href = `/room/${roomId}`;
      return;
    }
    phase = g.phase;
    if(g.chat_deadline){ chatDeadline = g.chat_deadline; ensureTimer(); }
    else if(inPostgame){ chatDeadline = state.postgame_deadline; ensureTimer(); }
    if(Array.isArray(g.chat_log)){
      // sync minimal (replace) to avoid duplicates
      if(logEl){ logEl.innerHTML=''; g.chat_log.forEach(addChat); }
    }
    if(readyIndicator){
      const ready = g.ready_players ? g.ready_players.length : 0;
      readyIndicator.textContent = `بازیکنان آماده: ${ready}/${state.game.players ? Object.keys(state.game.players).length : state.player_count || ''}`;
      readyIndicator.setAttribute('data-ready-count', ready);
    }
    if(personaTag && state.you){
      // persona is per session; we need to fetch separately if not cached
      fetch('/state/'+roomId).then(r=>r.json()).then(s=>{
        try{
          const p = window.sessionStorage.getItem('chat_persona');
          if(p){ personaTag.textContent = 'دستیار: '+p; }
          else {
            // try to infer from last bot message
            if(g.chat_log && g.chat_log.length){
              for(let i=g.chat_log.length-1;i>=0;i--){
                const msg = g.chat_log[i];
                if(['Sherlock Holmes','Hercule Poirot','Columbo','Miss Marple','Mentalist'].includes(msg.player)){
                  personaTag.textContent = 'دستیار: '+msg.player; window.sessionStorage.setItem('chat_persona', msg.player); break;
                }
              }
            }
          }
        }catch(_e){}
      });
    }
  }

  // Polling (every 2s) for state + passive chat updates
  let pollInt=null; let lastSig='';
  function sig(state){ try { return JSON.stringify({g: state.game, pd: state.postgame_deadline}); } catch(e){ return ''; } }
  function poll(){
    fetch(`/state/${roomId}`).then(r=>r.ok?r.json():null).then(data=>{
      if(!data || data.error) return;
      const s = sig(data);
      if(s !== lastSig){ lastSig = s; renderState(data); }
    }).catch(()=>{});
  }
  function startPoll(){ if(pollInt) return; pollInt = setInterval(poll, 2000); poll(); }
  startPoll();

  // -------------- Inactivity heartbeat --------------
  let hbTimer=null; function sendPing(){ fetch(`/ping/${roomId}`, {method:'POST'}).catch(()=>{}); }
  function startHB(){ if(hbTimer) return; hbTimer = setInterval(sendPing, 30000); sendPing(); }
  document.addEventListener('visibilitychange', ()=>{ if(document.visibilityState==='visible') startHB(); });
  window.addEventListener('beforeunload', sendPing);
  startHB();

  if(form){
    form.addEventListener('submit', e=>{
      e.preventDefault();
      const msg = input.value.trim(); if(!msg) return;
      const fd = new FormData(); fd.append('msg', msg);
      fetch(`/chat/send/${roomId}`, {method:'POST', body: fd})
        .then(r=>r.json())
        .then(d=>{ if(!d.error){ input.value=''; if(d.entry) addChat(d.entry); renderState(d.state);} else alert(d.error); });
    });
  }
  if(readyBtn){
    readyBtn.addEventListener('click', ()=>{
      fetch(`/chat/ready/${roomId}`, {method:'POST'}).then(r=>r.json()).then(d=>{ if(d.error) alert(d.error); else renderState(d.state); });
    });
  }

  if(botBtn){
    botBtn.addEventListener('click', ()=>{
      if(botBtn.getAttribute('data-busy')==='1') return;
      botBtn.setAttribute('data-busy','1');
      const oldTxt = botBtn.textContent; botBtn.textContent = '...';
      fetch(`/chat/bot_reply/${roomId}`, {method:'POST'})
        .then(r=>r.json())
        .then(d=>{
          botBtn.removeAttribute('data-busy'); botBtn.textContent = oldTxt;
          if(d.error){ alert(d.error); return; }
          if(d.entry) addChat(d.entry);
          if(d.persona){ window.sessionStorage.setItem('chat_persona', d.persona); if(personaTag) personaTag.textContent = 'دستیار: '+d.persona; }
          if(d.state) renderState(d.state);
        })
        .catch(()=>{ botBtn.removeAttribute('data-busy'); botBtn.textContent = oldTxt; });
    });
  }

  // Passive server timer tick (in case SSE lag) every 5s
  setInterval(()=>{ if(phase==='CHAT'){ fetch(`/chat/tick/${roomId}`).then(()=>{}); } }, 5000);
})();

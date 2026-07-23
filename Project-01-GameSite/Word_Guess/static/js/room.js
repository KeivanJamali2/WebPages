(function(){
  const area = document.getElementById('game-area');
  if(!area) return;
  const roomId = area.getAttribute('data-room-id');

  const askForm = document.getElementById('ask-form');
  const guessForm = document.getElementById('guess-form');
  const qInput = document.getElementById('question-input');
  const gInput = document.getElementById('guess-input');
  const qLog = document.getElementById('questions-log');
  const gLog = document.getElementById('guesses-log');
  const questionsRemainingEl = document.getElementById('questions-remaining');
  const winnerEl = document.getElementById('winner');
  const revealBox = document.getElementById('reveal-box');
  const revealBtn = document.getElementById('reveal-btn');
  const revealedWordEl = document.getElementById('revealed-word');
  const perPlayerStatusEl = document.getElementById('per-player-status');
  const startBox = document.getElementById('start-box');
  const statusBox = document.getElementById('status-box');
  const qaBox = document.getElementById('qa-box');
  const guessBox = document.getElementById('guess-box');
  const roundPhaseEl = document.getElementById('round-phase');
  // Dynamic players list ("همراهان") support
  const playersAside = document.querySelector('.players-panel');
  const playersListEl = playersAside ? playersAside.querySelector('.players-list') : null;
  let postgameBadge = null;
  // Chat handled on separate page now

  let currentPhase = null;
  let chatRedirected = false;

  function fmtTimeLeft(deadline){
    if(!deadline) return '--:--';
    const now = Date.now()/1000;
    let s = Math.max(0, Math.floor(deadline - now));
    const m = Math.floor(s/60); s = s % 60;
    return `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
  }

  function addChatEntry(_entry){ /* no-op in room view */ }

  // Wrapper over new procedural sound manager (fallback to inline beep)
  function playBeep(kind='beep'){
    if(window.WGSounds){ window.WGSounds.play(kind); return; }
    try { // fallback
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator(); const g = ctx.createGain();
      o.type='sine'; o.frequency.value = 660; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.18, ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.22);
      o.start(); o.stop(ctx.currentTime + 0.22);
    } catch(_e){}
  }

  function animateListItem(li){
    if(!li) return;
    if(window.WGFx){ window.WGFx.pulse(li); }
  }

  function addQuestionToLog(entry){
    if(!qLog) return;
    const li = document.createElement('li');
    const ansSpan = document.createElement('span');
    ansSpan.className = 'ans ' + (entry.answer_bool ? 'yes':'no');
    ansSpan.textContent = entry.answer_bool ? 'بله':'خیر';
    const qSpan = document.createElement('span');
    qSpan.textContent = `${entry.player}: ${entry.question}`;
    li.appendChild(qSpan); li.appendChild(ansSpan); qLog.prepend(li);
    animateListItem(li);
    if(entry.answer_bool) playBeep('beep'); else playBeep('fail');
  }

  function addGuessToLog(entry){
    if(!gLog) return;
    const li = document.createElement('li');
    const ansSpan = document.createElement('span');
    ansSpan.className = 'ans ' + (entry.correct ? 'yes':'no');
    ansSpan.textContent = entry.correct ? '✅':'❌';
    const gSpan = document.createElement('span');
    gSpan.textContent = `${entry.player}: ${entry.guess}`;
    li.appendChild(gSpan); li.appendChild(ansSpan); gLog.prepend(li);
    animateListItem(li);
    if(entry.correct){ playBeep('success'); if(window.WGConfetti) window.WGConfetti.launch(); }
    else playBeep('fail');
  }

  function renderState(state){
    if(!state) return;
    if(state.started){
      if(startBox) startBox.style.display='none';
      if(statusBox) statusBox.style.display='block';
      if(qaBox) qaBox.style.display='block';
      if(guessBox) guessBox.style.display='block';
    }
    // Update players list if present
    if(playersListEl && Array.isArray(state.players)){
      // Build signature including suspension mapping for accurate diffing
      const suspendedMap = state.suspended_players || {};
      const currentSig = playersListEl.getAttribute('data-sig');
      const nextSig = state.players.map(p=> p + (suspendedMap[p]?':S'+suspendedMap[p]:'')).join('|');
      if(currentSig !== nextSig){
        playersListEl.innerHTML='';
        state.players.forEach(p=>{
          const li=document.createElement('li');
          li.className='player-chip';
            if(suspendedMap[p]){
              li.classList.add('suspended');
              const deadline = suspendedMap[p];
              const timerSpan = document.createElement('span');
              timerSpan.className='suspend-count';
              const updateTimer=()=>{
                const now = Date.now()/1000; let left = Math.max(0, Math.floor(deadline - now));
                const m=Math.floor(left/60); const s=left%60; timerSpan.textContent=`${m}:${s.toString().padStart(2,'0')}`;
                if(left<=0){ clearInterval(intv); timerSpan.textContent='0:00'; }
              };
              updateTimer();
              const intv=setInterval(updateTimer,1000);
              li.appendChild(timerSpan);
            }
          li.appendChild(document.createTextNode(p));
          playersListEl.appendChild(li);
        });
        playersListEl.setAttribute('data-sig', nextSig);
      }
    }
    // Show reset reason (one-time alert) if present and changed
    if(state.last_reset_reason && renderState._lastResetReason !== state.last_reset_reason){
      const reason = state.last_reset_reason;
      let msg='';
      if(reason==='suspend_timeout') msg='بازی به علت عدم بازگشت یکی از بازیکنان ریست شد.';
      else if(reason==='inactive_player') msg='بازی به علت عدم فعالیت بازیکن ریست شد.';
      else if(reason==='manual') msg='اتاق به صورت دستی ریست شد.';
      if(msg) try{ window.WGSounds && window.WGSounds.play('fail'); alert(msg); }catch(_e){}
      renderState._lastResetReason = reason;
    }
    // Post-game countdown UI
    if(state.postgame_deadline){
      const now = Date.now()/1000;
      const left = Math.max(0, Math.floor(state.postgame_deadline - now));
      if(!postgameBadge){
        postgameBadge = document.createElement('div');
        postgameBadge.className = 'postgame-badge';
        postgameBadge.innerHTML = '<span class="label">پایان بازی - ریست در</span><span class="count" id="pg-count">'+left+'</span>';
        if(statusBox) statusBox.appendChild(postgameBadge);
      }
      const cnt = postgameBadge.querySelector('#pg-count'); if(cnt) cnt.textContent = left;
      if(!renderState._pgTimer){
        renderState._pgTimer = setInterval(()=>{
          const now2 = Date.now()/1000; const left2 = Math.max(0, Math.floor(state.postgame_deadline - now2));
          const cnt2 = postgameBadge.querySelector('#pg-count'); if(cnt2) cnt2.textContent = left2;
          if(left2<=0){ clearInterval(renderState._pgTimer); renderState._pgTimer=null; }
        }, 1000);
      }
    } else if(postgameBadge){
      // Removed after reset
      postgameBadge.remove(); postgameBadge=null; if(renderState._pgTimer){ clearInterval(renderState._pgTimer); renderState._pgTimer=null; }
    }
    const game = state.game;
    if(game){
      // Multi-mode additions
      if(roundPhaseEl){
        let txt = '';
        if(game.round) txt += `دور ${game.round} | `;
        if(game.phase) txt += `فاز: ${game.phase}`;
        roundPhaseEl.textContent = txt;
      }
      if(game.phase){
        currentPhase = game.phase;
        if(currentPhase === 'CHAT' && !chatRedirected){
          chatRedirected = true;
          window.location.href = `/chat/${roomId}`;
          return; // stop further rendering
        }
      }
      if(questionsRemainingEl){
        if(game.questions_remaining_shared !== null && game.questions_remaining_shared !== undefined){
          questionsRemainingEl.textContent = game.questions_remaining_shared;
        } else {
          questionsRemainingEl.textContent = '—';
        }
      }
      // Progress ring now reflects average per-player question usage this round
      const ring = document.querySelector('[data-ring]');
      if(ring && game.players){
        // Determine per-player quota from limits (questions_left + questions_used)
        // We take first player as reference since all have same quota in multi mode.
        const players = Object.keys(game.players);
        if(players.length){
          const sample = game.players[players[0]];
          const perPlayerTotal = (sample.questions_left ?? 0) + (sample.questions_used ?? 0);
          if(perPlayerTotal > 0){
            // Compute average used across players for smoother feel
            let usedSum = 0;
            players.forEach(p=>{ usedSum += (game.players[p].questions_used ?? 0); });
            const avgUsed = usedSum / players.length;
            const pct = Math.min(1, Math.max(0, avgUsed / perPlayerTotal));
            const circumference = 2 * Math.PI * 52; // r=52 from SVG
            const offset = circumference * pct;
            ring.style.strokeDasharray = circumference.toFixed(2);
            ring.style.strokeDashoffset = offset.toFixed(2);
            if(renderState._lastPct !== undefined && Math.abs(renderState._lastPct - pct) > 0.0001){
              ring.animate([
                { filter:'drop-shadow(0 0 4px rgba(255,210,140,.5))' },
                { filter:'drop-shadow(0 0 14px rgba(255,210,140,.85))' },
                { filter:'drop-shadow(0 0 4px rgba(255,210,140,.5))' }
              ], { duration: 1100, easing:'ease-in-out' });
            }
            renderState._lastPct = pct;
          }
        }
      }
      if(winnerEl){
        winnerEl.textContent = game.winner || '—';
      }
      if(game.is_over && revealBox){
        if(revealBox.style.display !== 'block'){ // just transitioned
          if(window.WGConfetti) window.WGConfetti.launch({count:55});
          playBeep('reveal');
          // Add celebration class to body for subtle global effects (no scroll)
          document.body.classList.add('game-finished');
        }
        revealBox.style.display='block';
      }
      if(perPlayerStatusEl){
        // Support both legacy simple & new multi data shape
        if(game.players){
          let html = '<table><thead><tr><th>بازیکن</th><th>سوال مصرف‌شده</th><th>سوال باقی</th><th>حدس باقی</th></tr></thead><tbody>';
          Object.keys(game.players).forEach(p=>{
            const ps = game.players[p];
            html += `<tr><td>${p}</td><td>${ps.questions_used ?? '—'}</td><td>${ps.questions_left ?? '—'}</td><td>${ps.guesses_left ?? (ps.guesses_remaining || '—')}</td></tr>`;
          });
          html += '</tbody></table>';
          perPlayerStatusEl.innerHTML = html;
        } else {
          const qRemain = game.questions_remaining_per_player || {};
          const qUsed = game.questions_used_per_player || {};
          const gRemain = game.guesses_remaining_per_player || {};
          let html = '<table><thead><tr><th>بازیکن</th><th>سوال مصرف‌شده</th><th>سوال باقی</th><th>حدس باقی</th></tr></thead><tbody>';
          Object.keys(gRemain).forEach(p=>{
            html += `<tr><td>${p}</td><td>${qUsed[p] ?? '—'}</td><td>${qRemain[p] ?? '—'}</td><td>${gRemain[p] ?? '—'}</td></tr>`;
          });
          html += '</tbody></table>';
          perPlayerStatusEl.innerHTML = html;
        }
      }
    }
  }

  // Polling loop replacement for real-time updates
  let pollInterval = null;
  let lastSerialized = '';
  function shallowSerialize(state){
    // Include sorted players list so that a rapid leave+join that keeps count the same still triggers re-render
    try { return JSON.stringify({g: state.game, p: state.player_count, started: state.started, pd: state.postgame_deadline, pls: (state.players||[]).slice().sort()}); } catch(e){ return ''; }
  }
  function pollOnce(){
    fetch(`/state/${roomId}`)
      .then(r=>r.ok?r.json():null)
      .then(data=>{
        if(!data || data.error) return;
        const s = shallowSerialize(data);
        if(s !== lastSerialized){
          lastSerialized = s;
          renderState(data);
        }
      })
      .catch(()=>{});
  }
  function startPolling(){ if(pollInterval) return; pollInterval = setInterval(pollOnce, 2000); pollOnce(); }
  startPolling();

  // ---------------- Inactivity heartbeat ----------------
  let hbTimer = null;
  function sendPing(){
    fetch(`/ping/${roomId}`, {method:'POST'}).catch(()=>{});
  }
  function startHeartbeat(){
    if(hbTimer) return; hbTimer = setInterval(sendPing, 30000); // 30s
    sendPing();
  }
  function stopHeartbeat(){ if(hbTimer){ clearInterval(hbTimer); hbTimer=null; } }
  document.addEventListener('visibilitychange', ()=>{
    if(document.visibilityState === 'visible'){ startHeartbeat(); }
    else { /* we still keep timer to allow brief tab switches; optionally pause */ }
  });
  window.addEventListener('beforeunload', ()=>{ sendPing(); });
  startHeartbeat();

  // Form submit handlers (no immediate log append; rely on SSE echo)
  if(askForm){
    askForm.addEventListener('submit', function(e){
      e.preventDefault();
      const q = qInput.value.trim();
      if(!q) return;
      const fd = new FormData(); fd.append('question', q);
      fetch(`/ask/${roomId}`, {method:'POST', body: fd})
        .then(r=>r.json())
        .then(data=>{ if(data.error){ alert(data.error); } else { qInput.value=''; addQuestionToLog({player:data.player, question:data.question, answer_bool:data.answer_bool}); renderState(data.state);} });
    });
  }
  if(guessForm){
    guessForm.addEventListener('submit', function(e){
      e.preventDefault();
      const g = gInput.value.trim();
      if(!g) return;
      const fd = new FormData(); fd.append('guess', g);
      fetch(`/guess/${roomId}`, {method:'POST', body: fd})
        .then(r=>r.json())
        .then(data=>{ if(data.error){ alert(data.error); } else { gInput.value=''; addGuessToLog({player:data.player, guess:data.guess, correct:data.correct}); renderState(data.state);} });
    });
  }
  if(revealBtn){
    revealBtn.addEventListener('click', function(){
      if(revealBtn.disabled) return;
      revealBtn.disabled = true;
      fetch(`/reveal/${roomId}`, {method:'POST'})
        .then(r=>r.json().catch(()=>null))
        .then(data=>{
          if(!data || data.error){
            // Re-enable only if still over but server rejected (e.g., race condition)
            revealBtn.disabled = false;
            if(data && data.error){
              // Provide gentle feedback instead of silent fail
              alert(data.error);
            }
            return;
          }
          if(revealedWordEl){
            revealedWordEl.textContent = data.word;
            // retrigger animation
            revealedWordEl.classList.remove('revealed-show');
            void revealedWordEl.offsetWidth; // force reflow
            revealedWordEl.classList.add('revealed-show');
          }
          // Hide button after successful reveal
          revealBtn.style.display = 'none';
        })
        .catch(()=>{ revealBtn.disabled = false; });
    });
  }

  // Minimal timer tick removal; chat handled elsewhere
})();

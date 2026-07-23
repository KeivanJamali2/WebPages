// Lightweight polling chat client for Word Sync Game
// Keeps aesthetic consistent with existing UI; uses fetch polling.

import { toast } from './ui.js';
import { sounds } from './sounds.js';

const POLL_MS = 1800;
let lastId = 0;
let currentGeneration = 1; // server-provided chat generation marker
// Track already rendered message ids to avoid occasional duplicates when
// an in-flight poll (started before local optimistic append) returns the
// just-sent message. Without this, the race can cause a second DOM append.
const seenIds = new Set();
let firstBatchLoaded = false; // suppress sound for initial history load
let youName = null; // current player's name (to suppress self message sound)
let polling = false;
let scroller; let listEl; let form; let input; let toggleBtn; let panel; let replyPreview; let cancelReplyBtn; let llmBtn;
let personaToggle; let personaDrawer; let personaCurrentSpan; let currentPersona = '';
let replyTarget = null; // {id, player, text}
let unread = false;
let resetBtn; // per-user chat reset button

// Detect if a string contains RTL (Persian/Arabic) characters
function detectRTL(str){
  return /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/.test(str);
}

function esc(str){
  return str.replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[c] || c);
}

async function api(path, opts={}){
  const res = await fetch(path, { credentials:'same-origin', ...opts, headers: { 'Content-Type':'application/json', ...(opts.headers||{}) } });
  return res.json();
}

function renderMessages(msgs){
  if(!msgs.length) return;
  const frag = document.createDocumentFragment();
  let playNotify = false;
  msgs.forEach(m=>{
    // Skip if we've already rendered this id
    if(seenIds.has(m.id)){
      // still advance lastId in case this was the newest id (e.g., after reload)
      lastId = Math.max(lastId, m.id);
      return; }
    const li = document.createElement('div');
    li.className = 'chat-msg';
    if(m.player && m.player.startsWith('🤖')){ li.classList.add('bot'); }
    li.dataset.id = m.id;
    const time = new Date(m.ts*1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    let replyHtml = '';
    if(m.reply_preview){
      replyHtml = `<div class="reply-ref" data-ref="${m.reply_preview.id}"><span class="ref-who">${esc(m.reply_preview.player)}</span>: <span class="ref-text">${esc(m.reply_preview.text)}</span></div>`;
    }
  // Preserve multiline by converting newlines to <br>
  const renderedText = esc(m.text).replace(/\n/g,'<br>');
  li.innerHTML = `${replyHtml}<span class="who">${esc(m.player)}</span><span class="text">${renderedText}</span><span class="time">${time}</span>`;
    // Direction detection (Persian / Arabic range -> rtl else ltr)
    const isRTL = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/.test(m.text);
    li.dir = isRTL ? 'rtl' : 'ltr';
    li.classList.add(isRTL ? 'rtl' : 'ltr');
    // click to set reply target
    li.addEventListener('click', (e)=>{
      // avoid if clicked inside a link later etc.
      setReplyTarget({ id: m.id, player: m.player, text: m.text });
    });
    frag.appendChild(li);
    lastId = Math.max(lastId, m.id);
    seenIds.add(m.id);
    // Determine if we should play a sound: skip first batch, skip if from self
    if(firstBatchLoaded && youName && m.player !== youName){
      playNotify = true;
    }
  });
  listEl.appendChild(frag);
  // autoscroll if near bottom
  if(scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 120){
    scroller.scrollTop = scroller.scrollHeight;
  } else {
    // new messages but user not at bottom -> mark unread
    setUnread(true);
  }
  if(playNotify){
    sounds.play('chat');
  }
  if(!firstBatchLoaded){ firstBatchLoaded = true; }
}

async function poll(){
  if(polling){ setTimeout(poll, POLL_MS); return; }
  polling = true;
  try {
    const data = await api(`/api/chat/since?after=${lastId}`);
    if(data.ok){
      // Detect generation reset
      if(data.generation && data.generation !== currentGeneration){
        // Clear everything locally
        currentGeneration = data.generation;
        lastId = 0; seenIds.clear(); listEl.innerHTML=''; firstBatchLoaded = false; setUnread(false);
      }
      renderMessages(data.messages);
    }
  } catch(e){ console.warn('chat poll error', e); }
  finally { polling = false; setTimeout(poll, POLL_MS); }
}

function setReplyTarget(target){
  replyTarget = target;
  if(!target){
    replyPreview.classList.add('hidden');
    replyPreview.querySelector('.rp-text').textContent = '';
    return;
  }
  replyPreview.classList.remove('hidden');
  replyPreview.querySelector('.rp-text').textContent = `${target.player}: ${target.text.slice(0,120)}`;
  input.focus();
}

function setUnread(v){
  unread = v;
  if(!toggleBtn) return;
  if(unread){ toggleBtn.classList.add('has-unread'); }
  else { toggleBtn.classList.remove('has-unread'); }
}

function markRead(){
  // called when panel opened and scrolled to bottom
  if(panel.classList.contains('collapsed')) return;
  const nearBottom = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 10;
  if(nearBottom) setUnread(false);
}

function init(){
  panel = document.getElementById('chatPanel');
  if(!panel) return; // not on game page
  scroller = panel.querySelector('.chat-scroll');
  listEl = panel.querySelector('.chat-messages');
  form = panel.querySelector('#chatForm');
  input = form.querySelector('textarea');
  toggleBtn = document.getElementById('chatToggle');

  toggleBtn.addEventListener('click', ()=>{
    panel.classList.toggle('collapsed');
    toggleBtn.classList.toggle('open');
    if(!panel.classList.contains('collapsed')){
      scroller.scrollTop = scroller.scrollHeight;
      markRead();
    }
  });

  llmBtn = document.getElementById('llmTalkBtn');
  if(llmBtn){
    llmBtn.addEventListener('click', async ()=>{
      llmBtn.disabled = true; llmBtn.textContent = '...';
      try {
        const res = await api('/api/chat/llm_talk', { method: 'POST', body: JSON.stringify({ persona: currentPersona }) });
        if(res.ok){ renderMessages([res.message]); markRead(); }
        else { toast(res.error || 'LLM error', { tone:'bad' }); }
      } catch(e){ toast('خطا در ارتباط با سرور', { tone:'bad' }); }
      finally { llmBtn.disabled = false; llmBtn.textContent = '🤖'; }
    });
  }

  // Persona drawer wiring (dynamic)
  personaToggle = document.getElementById('personaToggle');
  personaDrawer = document.getElementById('personaDrawer');
  personaCurrentSpan = document.getElementById('personaCurrent');
  if(personaToggle && personaDrawer){
    personaToggle.addEventListener('click', ()=>{
      personaDrawer.classList.toggle('hidden');
    });
    // Fetch allowed personas from backend
    fetch('/api/chat/personas').then(r=>r.json()).then(data=>{
      if(!data || !data.ok) return;
      const list = Array.isArray(data.allowed) ? data.allowed : [];
      const def = data.default || (list[0] || '');
      const optsWrap = personaDrawer.querySelector('.persona-options');
      optsWrap.innerHTML='';
      list.forEach(name=>{
        const btn = document.createElement('button');
        btn.type='button';
        btn.className='persona-option';
        btn.setAttribute('data-persona', name);
        btn.textContent = name;
        btn.addEventListener('click', ()=>{
          currentPersona = name;
          personaCurrentSpan.textContent = name;
          optsWrap.querySelectorAll('.persona-option').forEach(o=> o.classList.toggle('active', o===btn));
          personaDrawer.classList.add('hidden');
          toast('Persona: '+name, { tone:'neutral' });
        });
        optsWrap.appendChild(btn);
      });
      // Set default
      currentPersona = def;
      personaCurrentSpan.textContent = def;
      // mark active
      const activeBtn = optsWrap.querySelector(`.persona-option[data-persona="${CSS.escape(def)}"]`);
      if(activeBtn) activeBtn.classList.add('active');
    }).catch(()=>{});
    // Close when clicking outside
    document.addEventListener('click', (e)=>{
      if(!personaDrawer.classList.contains('hidden')){
        if(!personaDrawer.contains(e.target) && e.target !== personaToggle){
          personaDrawer.classList.add('hidden');
        }
      }
    });
  }

  replyPreview = panel.querySelector('.reply-preview');
  cancelReplyBtn = replyPreview.querySelector('.rp-cancel');
  cancelReplyBtn.addEventListener('click', (e)=>{ e.preventDefault(); setReplyTarget(null); });

  // Reset button logic (per-user clear)
  resetBtn = document.getElementById('chatResetBtn');
  if(resetBtn){
    resetBtn.addEventListener('click', async ()=>{
      if(!confirm('Clear chat for ALL players? This cannot be undone.')) return;
      try {
        resetBtn.disabled = true;
        const r = await api('/api/chat/reset_all', { method:'POST', body:'{}' });
        if(r.ok){
          currentGeneration = r.generation;
          lastId = 0; seenIds.clear(); listEl.innerHTML=''; firstBatchLoaded = false; setUnread(false);
          toast('Chat globally cleared', { tone:'warn' });
        } else { toast(r.error || 'Reset failed', { tone:'bad' }); }
      } catch(e){ toast('Reset error', { tone:'bad' }); }
      finally { resetBtn.disabled = false; }
    });
  }

  scroller.addEventListener('scroll', markRead, { passive:true });

  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const text = input.value.trim();
    if(!text) return;
    const payload = { text };
    if(replyTarget){ payload.reply_to = replyTarget.id; }
    const r = await api('/api/chat/send', { method:'POST', body: JSON.stringify(payload) });
    if(r.ok){
      input.value=''; renderMessages([r.message]); setReplyTarget(null); markRead();
      input.removeAttribute('dir'); input.classList.remove('rtl','ltr');
    }
    else { toast(r.error || 'Chat error', { tone:'bad' }); }
  });

  // Auto direction for input as user types
  // Input direction + autosize
  function autoSize(){
    if(!input) return;
    input.style.height = 'auto';
    const maxHeight = 140; // px limit before scrolling
    input.style.height = Math.min(input.scrollHeight, maxHeight) + 'px';
    input.classList.toggle('scrolling', input.scrollHeight > maxHeight);
  }
  input.addEventListener('input', ()=>{
    const v = input.value;
    const trimmed = v.trim();
    if(!trimmed){ input.removeAttribute('dir'); input.classList.remove('rtl','ltr'); }
    else {
      const rtl = detectRTL(trimmed);
      input.dir = rtl ? 'rtl' : 'ltr';
      input.classList.toggle('rtl', rtl);
      input.classList.toggle('ltr', !rtl);
    }
    autoSize();
  });
  // Key handling: Enter sends unless Shift
  input.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      form.requestSubmit();
    }
  });
  // Initialize size
  autoSize();

  // grab player name from game UI if present
  const youEl = document.getElementById('youName');
  if(youEl){
    youName = youEl.textContent.trim();
    // observe future changes (game state poll sets it asynchronously)
    const mo = new MutationObserver(()=>{ youName = youEl.textContent.trim(); });
    mo.observe(youEl, { characterData:true, subtree:true, childList:true });
  }
  poll();
}

// Initialize immediately if DOM is already parsed (script might be loaded after DOMContentLoaded)
if(document.readyState === 'loading'){
  window.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// =============================================================================
// EdGameClaw — AI Game-Based Learning Studio
// Created by Yuqi Hang (github.com/yh2072)
// https://github.com/yh2072/edgameclaw
// =============================================================================
if(typeof window.BACKGROUNDS==='undefined'||!window.BACKGROUNDS)window.BACKGROUNDS=[];
if(typeof window.CHAR_DRAW_FNS==='undefined'||!window.CHAR_DRAW_FNS)window.CHAR_DRAW_FNS={};
(function(){
  var orig=CanvasRenderingContext2D.prototype.arc;
  CanvasRenderingContext2D.prototype.arc=function(x,y,radius,startAngle,endAngle,anticlockwise){
    var r=Number(radius);
    if(!(r>0)||!isFinite(r))r=1e-6;
    return orig.call(this,x,y,r,startAngle,endAngle,anticlockwise);
  };
})();
const Audio=(()=>{
  const BASE=GAME.audioBase||'/assets/audio/';
  let bgmEnabled=true,sfxEnabled=true,bgmVolume=0.35,sfxVolume=0.5,currentBGM=null,audioCtxStarted=false;
  const _DEF_SFX={click:'Interface Sounds/Audio/click_003.ogg',select:'Interface Sounds/Audio/select_003.ogg',correct:'Interface Sounds/Audio/confirmation_002.ogg',wrong:'Interface Sounds/Audio/error_004.ogg',drop:'Interface Sounds/Audio/drop_004.ogg',powerUp:'Digital Audio/Audio/highUp.ogg',complete:'Interface Sounds/Audio/confirmation_004.ogg',chapterDone:'Digital Audio/Audio/pepSound2.ogg',maximize:'Interface Sounds/Audio/maximize_009.ogg',levelUp:'Music Jingles/Audio (Retro)/jingles-retro_00.ogg',reward:'Music Jingles/Audio (Retro)/jingles-retro_05.ogg',bookOpen:'RPG Audio/Audio/bookOpen.ogg',bookFlip:'RPG Audio/Audio/bookFlip1.ogg'};
  const _DEF_BGM={title:'Music Loops/Retro/Retro Mystic.ogg',dialog:'Music Loops/Retro/Retro Comedy.ogg',minigame:'Music Loops/Retro/Retro Beat.ogg',victory:'Music Loops/Loops/Cheerful Annoyance.ogg',explore:'Music Loops/Retro/Retro Reggae.ogg'};
  const _ga=GAME.audio||{};
  const SFX_MAP={};for(const k in _DEF_SFX)SFX_MAP[k]=BASE+((_ga.sfx&&_ga.sfx[k])||_DEF_SFX[k]);
  const BGM_MAP={};for(const k in _DEF_BGM)BGM_MAP[k]=BASE+((_ga.bgm&&_ga.bgm[k])||_DEF_BGM[k]);
  if(_ga.bgm)for(const k in _ga.bgm){if(!BGM_MAP[k])BGM_MAP[k]=BASE+_ga.bgm[k]}
  if(_ga.sfx)for(const k in _ga.sfx){if(!SFX_MAP[k])SFX_MAP[k]=BASE+_ga.sfx[k]}
  const cache={};
  function load(url){if(!cache[url]){cache[url]=new window.Audio(url);cache[url].preload='auto'}return cache[url]}
  function playSFX(n){if(!sfxEnabled||!SFX_MAP[n])return;const a=load(SFX_MAP[n]);a.volume=sfxVolume;a.currentTime=0;a.play().catch(()=>{})}
  function playBGM(n,opts){if(!BGM_MAP[n])return;stopBGM();currentBGM=load(BGM_MAP[n]);currentBGM.loop=!(opts&&opts.once);currentBGM.volume=bgmEnabled?bgmVolume:0;currentBGM.currentTime=0;currentBGM.play().catch(()=>{})}
  function stopBGM(){if(currentBGM){currentBGM.pause();currentBGM.currentTime=0;currentBGM=null}}
  function fadeOutBGM(ms){if(!currentBGM)return;const a=currentBGM,s=a.volume,st=Date.now();(function f(){const p=Math.min((Date.now()-st)/ms,1);a.volume=s*(1-p);if(p<1)requestAnimationFrame(f);else{a.pause();a.currentTime=0;if(currentBGM===a)currentBGM=null}})()}
  function toggleBGM(){bgmEnabled=!bgmEnabled;if(currentBGM)currentBGM.volume=bgmEnabled?bgmVolume:0;document.getElementById('btn-bgm').classList.toggle('muted',!bgmEnabled)}
  function toggleSFX(){sfxEnabled=!sfxEnabled;document.getElementById('btn-sfx').classList.toggle('muted',!sfxEnabled)}
  function ensureContext(){if(!audioCtxStarted){audioCtxStarted=true;playBGM('title')}}
  return{playSFX,playBGM,stopBGM,fadeOutBGM,toggleBGM,toggleSFX,ensureContext};
})();

const C=document.getElementById('main');const ctx=C.getContext('2d');
function px(x,y,c){ctx.fillStyle=c;ctx.fillRect(x,y,1,1)}
function rect(x,y,w,h,c){ctx.fillStyle=c;ctx.fillRect(x,y,w,h)}
function gpx(g,x,y,c){g.fillStyle=c;g.fillRect(x,y,1,1)}
function grect(g,x,y,w,h,c){g.fillStyle=c;g.fillRect(x,y,w,h)}

function createIcon(w,h,scale,drawFn){
  const c=document.createElement('canvas');c.width=w;c.height=h;
  c.style.width=(w*scale)+'px';c.style.height=(h*scale)+'px';
  c.style.imageRendering='pixelated';drawFn(c.getContext('2d'),w,h);return c;
}
function makeIcon(name,scale){
  if(!ICONS[name]){var fc=document.createElement('canvas');fc.width=1;fc.height=1;fc.style.display='none';return fc;}
  return createIcon(16,16,scale||2,ICONS[name]);
}
function makePortrait(name){
  if(!PORTRAITS[name])return document.createElement('canvas');
  return createIcon(32,32,3,PORTRAITS[name]);
}

const TOTAL_CHAPTERS=GAME.totalChapters||8;
(function(){const bar=document.getElementById('chapter-bar');for(let i=0;i<TOTAL_CHAPTERS;i++){const d=document.createElement('div');d.className='ch-dot';d.id='ch'+i;bar.appendChild(d)}})();

const CHAR_W=24,CHAR_H=36,CHAR_SCALE=4;
function createCharCanvas(drawFn){
  const c=document.createElement('canvas');c.width=CHAR_W;c.height=CHAR_H;
  c.style.width=(CHAR_W*CHAR_SCALE)+'px';c.style.height=(CHAR_H*CHAR_SCALE)+'px';
  c.className='char-sprite';drawFn(c.getContext('2d'));return c;
}

let particles=[];
function spawnParticles(x,y,type,count){
  const colors=GAME.particleColors||['#ffc0d0','#ff6a9a','#90e0a0','#80b0e0','#ffb0c0','#e0a0ff'];
  for(let i=0;i<count;i++){
    const a=Math.random()*Math.PI*2;const s=Math.random()*3+1;
    particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-(type==='confetti'?2:1),life:1,type,color:colors[Math.floor(Math.random()*colors.length)]});
  }
}
const pCanvas=document.getElementById('particles-canvas');const pCtx=pCanvas.getContext('2d');
function updateParticles(){
  pCtx.clearRect(0,0,768,576);
  particles=particles.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=0.08;p.life-=0.015;if(p.life<=0)return false;pCtx.globalAlpha=p.life;pCtx.fillStyle=p.color;pCtx.fillRect(p.x,p.y,p.type==='confetti'?4:3,p.type==='confetti'?4:3);return true});
  pCtx.globalAlpha=1;if(particles.length>0)requestAnimationFrame(updateParticles);
}
setInterval(()=>{if(particles.length>0)updateParticles()},50);

(function(){
  const inp=document.getElementById('player-name-input');
  const stored=localStorage.getItem('edgame_user_name');
  if(stored&&inp){inp.value=stored;inp.placeholder=stored}
  inp.addEventListener('keydown',e=>{if(e.key==='Enter')startGame()});
  async function tryAutoStart(){
    if(!window.auth||!GAME.courseId||!GAME.chunkId)return;
    try{
      await auth.ready();
      const r=await auth.canPlayGame(GAME.courseId,GAME.chunkId);
      if(!r.allowed){
        if(window.authUI){authUI.showPaywall(r.reason,GAME.courseId,GAME.chunkId,r)}
        return;
      }
    }catch(e){}
  }
  document.addEventListener('ahafrog-paywall-unlocked',function(ev){
    if(ev.detail&&ev.detail.courseId===GAME.courseId&&ev.detail.chunkId===GAME.chunkId&&typeof startGame==='function'){startGame()}
  });
  if(window._localeReady){window._localeReady.then(tryAutoStart)}else{tryAutoStart()}
})();

window._goNextGame=function(){
  var url=typeof GAME!=='undefined'&&GAME.nextGameUrl?GAME.nextGameUrl:null;
  if(!url){return;}
  var nextChunkId=(url.match(/(chunk-\d+)/)||[])[1]||null;
  if(!window.auth||!GAME.courseId||!nextChunkId){location.href=url;return;}
  auth.canPlayGame(GAME.courseId,nextChunkId).then(function(r){
    if(r&&r.allowed){location.href=url;return;}
    if(window.authUI){authUI.showPaywall((r&&r.reason)||'login_required',GAME.courseId,nextChunkId,r);}
    else{location.href=url;}
  }).catch(function(){location.href=url;});
};

let currentChapter=0,scriptIndex=0,gameState='title';
let chapterComplete=new Array(TOTAL_CHAPTERS).fill(false);
let _gameStartTime=Date.now();
const _ui=GAME.ui||{};
let playerName=GAME.defaultPlayerName||_ui.defaultPlayer||'研究员';
let currentSpeaker=null;let currentChars=[];
let _lastMiniGameType=null;

let totalXP=0,playerLevel=0,_mgScore=0,_minigameClosing=false;
const _chapterStars={};
const _LV_THRESHOLDS=[0,120,320,600,1000,1500];
const _LV_NAMES=_ui.levelNames||['✦ 初学者','✦✦ 探索者','✦✦✦ 学者','✧ 专家','✧✧ 大师','✧✧✧ 宗师'];
function _getLevel(xp){for(let i=_LV_THRESHOLDS.length-1;i>=0;i--)if(xp>=_LV_THRESHOLDS[i])return i;return 0}
function _getLevelName(lv){return _LV_NAMES[Math.min(lv,_LV_NAMES.length-1)]}
function _getStars(s){return s>=85?3:s>=55?2:s>=25?1:0}
function _starsText(n){return '★'.repeat(n)+'☆'.repeat(3-n)}

function _addXP(amount){
  const oldLv=playerLevel;totalXP+=amount;playerLevel=_getLevel(totalXP);
  _updateXPBar();
  if(playerLevel>oldLv)_showLevelUp(playerLevel);
}
function _updateXPBar(){
  const bar=document.getElementById('xp-bar');if(!bar)return;
  bar.style.display='block';
  const cur=_LV_THRESHOLDS[playerLevel]||0;
  const nxt=_LV_THRESHOLDS[playerLevel+1]||cur+100;
  const pct=Math.min(((totalXP-cur)/(nxt-cur))*100,100);
  const fill=document.getElementById('xp-fill');if(fill)fill.style.width=pct+'%';
  const label=document.getElementById('xp-label');
  if(label)label.textContent=(_ui.levelPrefix||'Lv.')+' '+(playerLevel+1)+' '+_getLevelName(playerLevel)+' · '+totalXP+' '+(_ui.xpUnit||'XP');
}

function _showLevelUp(lv){
  Audio.playSFX('levelUp');
  const ov=document.getElementById('level-up-overlay');if(!ov)return;
  const th=GAME.theme||{};
  ov.innerHTML='<div style="text-align:center;animation:levelUpPop 0.5s">'+
    '<div style="font-size:48px;margin-bottom:8px">🎉</div>'+
    '<div style="color:'+(th.highlight||'#ffc0d0')+';font-size:20px;letter-spacing:3px">'+(_ui.levelUp||'等级提升！')+'</div>'+
    '<div style="color:'+(th.accent||'#ff6a9a')+';font-size:32px;margin:8px 0;font-weight:bold">'+(_ui.levelPrefix||'Lv.')+' '+(lv+1)+'</div>'+
    '<div style="color:'+(th.success||'#90e0a0')+';font-size:15px">'+_getLevelName(lv)+'</div></div>';
  ov.style.display='flex';
  spawnParticles(384,250,'confetti',50);
  setTimeout(function(){ov.style.display='none';ov.innerHTML=''},2500);
}

function _showChapterTransition(ch){
  const ov=document.getElementById('chapter-transition');if(!ov)return;
  const th=GAME.theme||{};
  const _chFmt=(_ui.chapterFormat||'Ch.{n}').replace('{n}',ch+1);
  const title=(GAME.chapterTitles&&GAME.chapterTitles[ch])||_chFmt;
  ov.innerHTML='<div style="text-align:center;animation:chapterSlide 0.6s">'+
    '<div style="color:'+(th.muted||'#c080a0')+';font-size:10px;letter-spacing:4px;text-transform:uppercase;margin-bottom:6px">'+_chFmt+'</div>'+
    '<div style="color:'+(th.highlight||'#ffc0d0')+';font-size:22px;letter-spacing:2px;margin-bottom:12px">'+title+'</div>'+
    '<div style="width:40px;height:2px;background:'+(th.accent||'#ff6a9a')+';margin:0 auto 12px;border-radius:1px"></div>'+
    '<div style="color:'+(th.accent||'#ff6a9a')+';font-size:11px">'+(_ui.levelPrefix||'Lv.')+' '+(playerLevel+1)+' '+_getLevelName(playerLevel)+' · '+totalXP+' '+(_ui.xpUnit||'XP')+'</div></div>';
  ov.style.display='flex';
  Audio.playSFX('chapterDone');
  ov.onclick=function(){ov.style.display='none';ov.onclick=null};
  setTimeout(function(){ov.style.display='none';ov.onclick=null},2200);
}

function _showScoreFeedback(score,xpGained,stars){
  const fb=document.getElementById('score-feedback');if(!fb)return;
  const th=GAME.theme||{};
  const starColor=stars===3?(th.success||'#90e0a0'):stars===2?(th.accent||'#ff6a9a'):(th.muted||'#c080a0');
  fb.innerHTML='<div style="animation:scorePop 0.4s">'+
    '<div style="font-size:24px;color:'+starColor+';letter-spacing:4px">'+_starsText(stars)+'</div>'+
    '<div style="color:'+(th.highlight||'#ffc0d0')+';font-size:13px;margin-top:4px">+'+xpGained+' '+(_ui.xpUnit||'XP')+'</div></div>';
  fb.style.display='block';
  setTimeout(function(){fb.style.animation='scoreFloat 0.5s forwards';
    setTimeout(function(){fb.style.display='none';fb.style.animation='';fb.innerHTML=''},500)},1200);
}

function _updateChapterStars(ch,stars){
  _chapterStars[ch]=Math.max(_chapterStars[ch]||0,stars);
  const dot=document.getElementById('ch'+ch);
  if(dot){
    let s=dot.querySelector('.ch-stars');
    if(!s){s=document.createElement('div');s.className='ch-stars';dot.appendChild(s)}
    s.textContent=_starsText(_chapterStars[ch]);
  }
}

const CHAR_NAME_MAP={};
if(GAME.characters){
  Object.entries(GAME.characters).forEach(([id,info])=>{
    if(id==='player')CHAR_NAME_MAP.player=()=>playerName;
    else CHAR_NAME_MAP[id]=()=>info.name;
  });
}
if(!CHAR_NAME_MAP.player)CHAR_NAME_MAP.player=()=>playerName;

function personalizeText(text){return (text||'').replace(/\{player\}/g,playerName)}

function renderScene(bgIdx,chars){try{ctx.clearRect(0,0,128,96);if(BACKGROUNDS[bgIdx])BACKGROUNDS[bgIdx](ctx);renderCharacters(chars)}catch(e){console.error('renderScene error bg='+bgIdx,e)}}

let dialogTypingDone=false,dialogLocked=false,currentTypingInterval=null;
function showDialog(name,text){
  const displayName=personalizeText(name);const displayText=personalizeText(text);
  document.getElementById('dialog-box').style.display='block';
  document.getElementById('dialog-name').textContent=displayName;
  const textEl=document.getElementById('dialog-text');textEl.textContent='';
  dialogTypingDone=false;dialogLocked=true;highlightSpeaker(displayName);
  if(currentTypingInterval)clearInterval(currentTypingInterval);
  let i=0;currentTypingInterval=setInterval(()=>{
    if(i<displayText.length){textEl.textContent+=displayText[i];i++}
    else{clearInterval(currentTypingInterval);currentTypingInterval=null;dialogTypingDone=true}
  },18);
  setTimeout(()=>{dialogLocked=false},80);
}
function skipTyping(){
  if(currentTypingInterval){clearInterval(currentTypingInterval);currentTypingInterval=null}
  const cmd=SCRIPT[scriptIndex];
  if(cmd&&cmd.type==='dialog')document.getElementById('dialog-text').textContent=personalizeText(cmd.text);
  dialogTypingDone=true;
}
function hideDialog(){
  document.getElementById('dialog-box').style.display='none';
  if(currentTypingInterval){clearInterval(currentTypingInterval);currentTypingInterval=null}
  currentSpeaker=null;document.querySelectorAll('.char-wrapper').forEach(w=>w.classList.remove('speaking','silent'));
}
function hideCharacters(){document.getElementById('character-layer').innerHTML='';currentChars=[]}

function renderCharacters(chars){
  const layer=document.getElementById('character-layer');layer.innerHTML='';
  if(!chars||!chars.length){currentChars=[];return}
  currentChars=chars;
  chars.forEach(c=>{
    const w=document.createElement('div');w.className='char-wrapper';w.dataset.charId=c.id;
    w.style.left=((c.x/128)*768-(CHAR_W*CHAR_SCALE)/2)+'px';
    const nt=document.createElement('div');nt.className='char-name-tag';
    nt.textContent=CHAR_NAME_MAP[c.id]?CHAR_NAME_MAP[c.id]():'';
    w.appendChild(nt);
    if(CHAR_DRAW_FNS&&CHAR_DRAW_FNS[c.id]&&typeof CHAR_DRAW_FNS[c.id]==='function')w.appendChild(createCharCanvas(CHAR_DRAW_FNS[c.id]));
    layer.appendChild(w);
  });
  if(currentSpeaker)highlightSpeaker(currentSpeaker);
}

function highlightSpeaker(n){
  currentSpeaker=n;const ws=document.querySelectorAll('.char-wrapper');if(!ws.length)return;
  let sid=null;for(const[id,fn]of Object.entries(CHAR_NAME_MAP))if(fn()===n){sid=id;break}
  ws.forEach(w=>{w.classList.remove('speaking','silent');if(sid&&w.dataset.charId===sid)w.classList.add('speaking');else if(sid)w.classList.add('silent')});
}

function updateChapterBar(){
  for(let i=0;i<TOTAL_CHAPTERS;i++){
    const d=document.getElementById('ch'+i);d.className='ch-dot';
    if(chapterComplete[i])d.classList.add('done');else if(i===currentChapter)d.classList.add('active');
  }
}

function advanceDialog(){
  if(dialogLocked)return;
  if(gameState!=='dialog'){
    if(gameState==='playing'&&!_deferredProcessTimer&&scriptIndex<SCRIPT.length){processScript()}
    return;
  }
  if(!dialogTypingDone){skipTyping();Audio.playSFX('click');return}
  dialogLocked=true;Audio.playSFX('click');scriptIndex++;
  if(scriptIndex<SCRIPT.length)processScript();
}

// -- Created by Yuqi Hang (github.com/yh2072) --
function processScript(){
  try{
    if(scriptIndex>=SCRIPT.length){console.warn('processScript: scriptIndex',scriptIndex,'beyond SCRIPT length',SCRIPT.length);return}
    const cmd=SCRIPT[scriptIndex];
    if(!cmd){console.error('processScript: null cmd at index',scriptIndex);scriptIndex++;processScript();return}
    if(cmd.type==='bg'){renderScene(cmd.bg,cmd.chars);scriptIndex++;processScript()}
    else if(cmd.type==='chapter'){if(cmd.ch>0)chapterComplete[cmd.ch-1]=true;currentChapter=cmd.ch;updateChapterBar();_reportProgress(Math.min(0.9,(cmd.ch+1)/TOTAL_CHAPTERS));scriptIndex++;if(cmd.ch>0){_showChapterTransition(cmd.ch);_scheduleProcess(2300)}else{processScript()}}
    else if(cmd.type==='dialog'){gameState='dialog';dialogLocked=false;showDialog(cmd.name,cmd.text)}
    else if(cmd.type==='minigame'){hideDialog();hideCharacters();gameState='minigame';Audio.fadeOutBGM(400);setTimeout(()=>Audio.playBGM('minigame'),500);launchMiniGame(cmd.game)}
    else if(cmd.type==='end'){chapterComplete[TOTAL_CHAPTERS-1]=true;updateChapterBar();hideDialog();hideCharacters();Audio.fadeOutBGM(400);setTimeout(()=>Audio.playBGM('victory'),500);showEndScreen()}
    else{console.warn('processScript: unknown cmd type',cmd.type,'at',scriptIndex);scriptIndex++;processScript()}
  }catch(e){
    console.error('processScript error at index',scriptIndex,e);
    scriptIndex++;
    setTimeout(processScript,100);
  }
}

document.getElementById('dialog-click-area').addEventListener('click',advanceDialog);
document.getElementById('dialog-box').addEventListener('click',advanceDialog);

let _stuckCheckTimer=null,_deferredProcessTimer=null;
function _scheduleProcess(ms){if(_deferredProcessTimer)clearTimeout(_deferredProcessTimer);_deferredProcessTimer=setTimeout(function(){_deferredProcessTimer=null;processScript()},ms)}
function _checkStuck(){
  if(gameState==='title'||gameState==='dialog'||gameState==='minigame')return;
  if(_deferredProcessTimer)return;
  const dialogBox=document.getElementById('dialog-box');
  const mgOverlay=document.getElementById('mini-game-overlay');
  const chTrans=document.getElementById('chapter-transition');
  const scoreFb=document.getElementById('score-feedback');
  const dialogVisible=dialogBox&&dialogBox.style.display!=='none';
  const mgVisible=mgOverlay&&mgOverlay.style.display!=='none';
  const chVisible=chTrans&&chTrans.style.display!=='none';
  const scoreVisible=scoreFb&&scoreFb.style.display!=='none';
  if(!dialogVisible&&!mgVisible&&!chVisible&&!scoreVisible&&scriptIndex<SCRIPT.length){
    console.warn('Stuck-state detected: gameState='+gameState+' scriptIndex='+scriptIndex+' - auto-recovering');
    gameState='playing';dialogLocked=false;
    processScript();
  }
}
document.getElementById('game-container').addEventListener('click',function(){
  if(_stuckCheckTimer)clearTimeout(_stuckCheckTimer);
  _stuckCheckTimer=setTimeout(_checkStuck,500);
});

function startGame(){
  const ni=document.getElementById('player-name-input').value.trim();
  const storedName=localStorage.getItem('edgame_user_name');
  playerName=ni||storedName||GAME.defaultPlayerName||_ui.defaultPlayer||'研究员';
  if(storedName&&!ni)document.getElementById('player-name-input').value=playerName;
  CHAR_NAME_MAP.player=()=>playerName;
  Audio.ensureContext();Audio.playSFX('maximize');Audio.fadeOutBGM(600);
  setTimeout(()=>Audio.playBGM('dialog'),700);
  document.getElementById('title-screen').style.display='none';
  gameState='playing';scriptIndex=0;_gameStartTime=Date.now();updateChapterBar();processScript();
  _reportProgress('started');
  if(window.auth&&GAME.courseId&&GAME.chunkId){try{auth.recordGamePlay(GAME.courseId,GAME.chunkId)}catch(e){}}
  if(window.ahafrogAnalytics&&GAME.courseId&&GAME.chunkId){try{ahafrogAnalytics.trackGameStart(GAME.courseId,GAME.chunkId,{player:playerName})}catch(e){}}
}
function _reportProgress(status){
  try{
    const chunkId=GAME.chunkId||'';
    if(!chunkId)return;
    const prog=JSON.parse(localStorage.getItem('edgame_progress')||'{}');
    if(status==='started'){prog[chunkId]={progress:0.1,startedAt:new Date().toISOString()}}
    else if(status==='completed'){prog[chunkId]={completed:true,progress:1,completedAt:new Date().toISOString()}}
    else if(typeof status==='number'){prog[chunkId]=prog[chunkId]||{};prog[chunkId].progress=status}
    localStorage.setItem('edgame_progress',JSON.stringify(prog));
  }catch(e){}
}

function showEndScreen(){
  const ov=document.getElementById('mini-game-overlay');ov.style.display='flex';
  const th=GAME.theme||{};const endData=GAME.endScreen||{};
  const iconNames=endData.icons||[];
  const _endTitle=(_ui.endTitle||'✿ 恭喜你，{player}！✿').replace('{player}',playerName);
  const _endSub=(_ui.endSub||'{player}，你完成了全部 {total} 章！').replace('{player}',playerName).replace('{total}',TOTAL_CHAPTERS);
  var totalStars=0,maxStars=0;
  for(var k in _chapterStars){totalStars+=_chapterStars[k];maxStars+=3}
  if(!maxStars)maxStars=TOTAL_CHAPTERS*3;
  var avgPct=maxStars>0?Math.round((totalStars/maxStars)*100):0;
  var grade=avgPct>=90?'S':avgPct>=75?'A':avgPct>=60?'B':avgPct>=40?'C':'D';
  var gradeColor=avgPct>=90?(th.success||'#88ce02'):avgPct>=60?(th.accent||'#00e5c8'):(th.muted||'#7878a0');
  var starSummary='';
  for(var ci=0;ci<TOTAL_CHAPTERS;ci++){
    var s=_chapterStars[ci]||0;
    var cTitle=(GAME.chapterTitles&&GAME.chapterTitles[ci])?GAME.chapterTitles[ci]:(_ui.chapterFormat||'Ch.{n}').replace('{n}',ci+1);
    starSummary+='<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05)">'+
      '<span style="color:'+(th.muted||'#7878a0')+';font-size:11px">'+cTitle+'</span>'+
      '<span style="color:'+(s===3?(th.success||'#88ce02'):s===2?(th.accent||'#00e5c8'):(th.muted||'#7878a0'))+';font-size:12px;letter-spacing:2px">'+_starsText(s)+'</span></div>';
  }
  ov.innerHTML='<div style="text-align:center;max-width:560px;margin:0 auto">'+
    '<div class="mg-title" style="font-size:24px;margin-bottom:8px">'+_endTitle+'</div>'+
    '<div class="mg-instruction" style="font-size:14px;color:'+(th.success||'#90e0a0')+'">'+_endSub+'</div>'+
    '<div style="display:flex;gap:20px;justify-content:center;margin:16px 0;flex-wrap:wrap">'+
      '<div style="text-align:center;padding:12px 20px;background:rgba(255,255,255,0.03);border-radius:12px;border:1px solid '+(th.border||'#26263c')+'">'+
        '<div style="color:'+gradeColor+';font-size:36px;font-weight:bold">'+grade+'</div>'+
        '<div style="color:'+(th.muted||'#7878a0')+';font-size:10px">'+(_ui.grade||'评级')+'</div></div>'+
      '<div style="text-align:center;padding:12px 20px;background:rgba(255,255,255,0.03);border-radius:12px;border:1px solid '+(th.border||'#26263c')+'">'+
        '<div style="color:'+(th.success||'#88ce02')+';font-size:24px;font-weight:bold">'+totalStars+'/'+maxStars+'</div>'+
        '<div style="color:'+(th.muted||'#7878a0')+';font-size:10px">★ '+(_ui.stars||'星级')+'</div></div>'+
      '<div style="text-align:center;padding:12px 20px;background:rgba(255,255,255,0.03);border-radius:12px;border:1px solid '+(th.border||'#26263c')+'">'+
        '<div style="color:'+(th.accent||'#00e5c8')+';font-size:24px;font-weight:bold">'+(_ui.levelPrefix||'Lv.')+' '+(playerLevel+1)+'</div>'+
        '<div style="color:'+(th.muted||'#7878a0')+';font-size:10px">'+_getLevelName(playerLevel)+'</div></div>'+
    '</div>'+
    '<div style="max-width:400px;margin:0 auto 16px;text-align:left">'+starSummary+'</div>'+
    '<div id="end-icons" style="display:flex;gap:8px;justify-content:center;margin:12px 0;flex-wrap:wrap"></div>'+
    '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">'+
    '<button class="mg-btn" style="font-size:14px;padding:12px 32px;background:rgba(136,206,2,0.12);border-color:'+(th.success||'#88ce02')+';color:'+(th.success||'#88ce02')+';border-radius:20px;display:inline-flex;align-items:center;gap:6px" onclick="location.reload()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>'+(_ui.playAgain||'再玩一次')+'</button>'+
    (GAME.nextGameUrl?'<button class="mg-btn" style="font-size:14px;padding:12px 32px;background:rgba(0,229,200,0.12);border-color:'+(th.accent||'#00e5c8')+';color:'+(th.accent||'#00e5c8')+';border-radius:20px;display:inline-flex;align-items:center;gap:6px" onclick="window._goNextGame&&window._goNextGame()"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5,3 19,12 5,21"/></svg>'+(_ui.nextGame||'下一关')+'</button>':'')+
    (!GAME.nextGameUrl?'<a class="mg-btn" href="../.." style="font-size:14px;padding:12px 32px;border-color:'+(th.border||'#26263c')+';color:'+(th.muted||'#7878a0')+';border-radius:20px;text-decoration:none;pointer-events:auto;display:inline-flex;align-items:center;gap:6px"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'+(_ui.backToCourse||'返回课程')+'</a>':'')+
    '</div></div>';
  iconNames.forEach(function(n){var el=document.getElementById('end-icons');if(el)el.appendChild(makeIcon(n,3))});
  spawnParticles(384,200,'confetti',60);
  _reportProgress('completed');
  if(window.ahafrogAnalytics&&GAME.courseId&&GAME.chunkId){try{var _elapsed=Date.now()-(_gameStartTime||Date.now());var _avgScore=totalStars&&maxStars?Math.round(totalStars/maxStars*100):0;ahafrogAnalytics.trackGameComplete(GAME.courseId,GAME.chunkId,_avgScore,_elapsed)}catch(e){}}
  if(window.auth&&GAME.courseId&&GAME.chunkId){try{var _elapsed=Date.now()-(_gameStartTime||Date.now());var _avgScore=totalStars&&maxStars?Math.round(totalStars/maxStars*100):0;auth.recordLessonComplete(GAME.courseId,GAME.chunkId,_avgScore,Math.round(_elapsed/1000))}catch(e){}}
}

// -- Created by Yuqi Hang (github.com/yh2072) --
const MINIGAME_BUILDERS={};
function registerMinigame(type,builderFn){MINIGAME_BUILDERS[type]=builderFn}

function _buildMinigame(type,ov,mgData){
  if(MINIGAME_BUILDERS[type]){
    try{
      MINIGAME_BUILDERS[type](ov,mgData);ov.style.display='flex';
      // Safety delegate: if the sim's #done button fails to attach its own listener,
      // this catches the click and still calls closeMiniGame().
      (function(){var _sd=function(e){
        if(gameState!=='minigame')return;
        var t=e.target&&(e.target.id==='done'||(e.target.closest&&e.target.closest('[id="done"]')));
        if(t){ov.removeEventListener('click',_sd);closeMiniGame();}
      };ov.addEventListener('click',_sd);})();
    }
    catch(e){console.error('Minigame error:',type,e);try{if(GAME.courseId&&GAME.chunkId){fetch('/api/report-minigame-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({course_id:GAME.courseId,chunk_id:GAME.chunkId,minigame_type:type,error:String(e)})}).catch(()=>{});}}catch(_){}ov.innerHTML=`<div class="mg-title">⚠ ${type}</div><div class="mg-instruction" style="color:#ff6060">${_ui.loadError||'加载失败'}</div><button class="mg-btn" onclick="closeMiniGame()" style="pointer-events:auto">${_ui.skip||'跳过 →'}</button>`;ov.style.display='flex';}
  } else {
    ov.innerHTML=`<div class="mg-title">小游戏：${type}</div><div class="mg-instruction">该小游戏类型尚未实现。</div><button class="mg-btn" onclick="closeMiniGame()" style="pointer-events:auto">跳过 →</button>`;
  }
}

function _getMiniTutorial(type,data){
  if(type.startsWith('sim_'))return data&&data.subtitle?data.subtitle:null;
  return null;
}

let _mgIsFullscreen=false;
function _openReportModal(){
  if(!GAME.courseId||!GAME.chunkId)return;
  var overlay=document.createElement('div');
  overlay.id='mg-report-overlay';
  overlay.style.cssText='position:fixed;inset:0;z-index:300;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.7);backdrop-filter:blur(6px);pointer-events:auto';
  var inner=document.createElement('div');
  inner.style.cssText='background:rgba(28,18,32,0.98);border:1px solid rgba(255,100,150,0.3);border-radius:14px;padding:20px 24px;max-width:360px;width:90%';
  var th=GAME.theme||{};
  inner.innerHTML='<div class="mg-title" style="margin-bottom:12px;color:'+(th.highlight||'#ffc0d0')+'">报错 / Report</div>'+
    '<p style="font-size:12px;color:'+(th.muted||'#c080a0')+';margin-bottom:10px">问题描述（选填）</p>'+
    '<textarea id="mg-report-msg" placeholder="e.g. 画面卡住、题目显示不全…" style="width:100%;min-height:80px;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.05);color:#e8d8f0;font-size:13px;resize:vertical;box-sizing:border-box" maxlength="1000"></textarea>'+
    '<div style="margin-top:14px;display:flex;gap:10px;justify-content:flex-end">'+
    '<button type="button" id="mg-report-cancel" class="mg-btn" style="pointer-events:auto;padding:8px 16px">取消</button>'+
    '<button type="button" id="mg-report-submit" class="mg-btn" style="pointer-events:auto;padding:8px 20px;border-color:'+(th.success||'#90e0a0')+';color:'+(th.success||'#90e0a0')+'">提交</button></div>';
  overlay.appendChild(inner);
  document.body.appendChild(overlay);
  function closeReportModal(){var o=document.getElementById('mg-report-overlay');if(o)o.remove();}
  document.getElementById('mg-report-cancel').onclick=closeReportModal;
  document.getElementById('mg-report-submit').onclick=function(){
    var msg=(document.getElementById('mg-report-msg').value||'').trim().slice(0,1000);
    var payload={course_id:GAME.courseId,chunk_id:GAME.chunkId,minigame_type:_lastMiniGameType||'',error:'',message:msg};
    fetch('/api/report-minigame-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(function(){closeReportModal();if(typeof _ui!=='undefined'&&_ui.reportSubmitted)alert(_ui.reportSubmitted);else alert('已提交，感谢反馈');}).catch(function(){closeReportModal();alert('提交失败，请稍后再试');});
  };
}
function _attachSkipButton(){
  if(gameState!=='minigame')return;
  var s=document.getElementById('mg-skip-fixed');
  if(s){s.textContent=_ui.skip||'跳过 →';s.onclick=function(){closeMiniGame()};s.style.display='inline-block';}
  var r=document.getElementById('mg-report-fixed');
  if(r){r.textContent='报错';r.onclick=function(){_openReportModal()};r.style.display='inline-block';}
}
// -- Created by Yuqi Hang (github.com/yh2072) --
function launchMiniGame(type){
  _lastMiniGameType=type;
  const ov=document.getElementById('mini-game-overlay');ov.style.display='flex';ov.style.justifyContent='flex-start';ov.style.alignItems='flex-start';
  _mgIsFullscreen=false;

  const mgData=GAME.minigames[type]||{};
  const tutorialText=mgData._tutorial||_getMiniTutorial(type,mgData);
  if(tutorialText&&!mgData._tutorialSeen){
    mgData._tutorialSeen=true;
    const th=GAME.theme||{};
    ov.innerHTML='<div style="text-align:center;max-width:520px;margin:auto;padding:24px">'+
      '<div style="font-size:28px;margin-bottom:12px">📖</div>'+
      '<div class="mg-title" style="margin-bottom:12px">'+(mgData.title||type)+'</div>'+
      '<div style="color:'+(th.text||'#e8d8f0')+';font-size:13px;line-height:1.8;margin-bottom:20px;text-align:left;background:rgba(255,255,255,0.03);padding:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.06)">'+tutorialText+'</div>'+
      '<button class="mg-btn" id="tut-start" style="pointer-events:auto;padding:12px 36px;font-size:14px;border-color:'+(th.accent||'#ff6a9a')+'">'+(_ui.start||'开始')+ ' →</button></div>';
    ov.querySelector('#tut-start').addEventListener('click',function(){_buildMinigame(type,ov,mgData)});
  } else {
    _buildMinigame(type,ov,mgData);
  }
  _attachSkipButton();
}

function closeMiniGame(score){
  if(_minigameClosing)return;_minigameClosing=true;
  try{
    var skip=document.getElementById('mg-skip-fixed');if(skip)skip.style.display='none';
    var reportBtn=document.getElementById('mg-report-fixed');if(reportBtn)reportBtn.style.display='none';
    const ov=document.getElementById('mini-game-overlay');if(!ov){_minigameClosing=false;return;}
    let finalScore=typeof score==='number'?Math.min(100,Math.max(0,score)):(typeof _mgScore==='number'?_mgScore:0);
    _mgScore=0;
    if(finalScore===0&&_lastMiniGameType&&String(_lastMiniGameType).startsWith('sim_')){
      finalScore=70;
    }
    const stars=_getStars(finalScore);
    const xpGained=Math.round(finalScore*0.4+stars*10);
    _showMiniGameResult(finalScore,xpGained,stars,ov);
  }catch(e){
    console.error('closeMiniGame error',e);
    _minigameClosing=false;
    _advanceMiniGame(0,0,0);
  }
}

function _showMiniGameResult(finalScore,xpGained,stars,ov){
  const th=GAME.theme||{};
  const starColor=stars===3?(th.success||'#90e0a0'):stars===2?(th.accent||'#ff6a9a'):(th.muted||'#c080a0');
  ov.style.display='flex';ov.style.justifyContent='center';ov.style.alignItems='center';
  ov.innerHTML='<div style="text-align:center;padding:32px 40px;max-width:400px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;backdrop-filter:blur(12px)">'+
    '<div style="font-size:40px;color:'+starColor+';letter-spacing:8px;margin-bottom:16px;animation:scorePop 0.5s">'+_starsText(stars)+'</div>'+
    '<div style="color:'+(th.highlight||'#ffc0d0')+';font-size:28px;font-weight:bold;margin-bottom:4px">'+finalScore+'<span style="font-size:14px;margin-left:4px">'+(_ui.scoreUnit||'pts')+'</span></div>'+
    '<div style="color:'+(th.success||'#90e0a0')+';font-size:15px;margin-bottom:24px">+'+xpGained+' '+(_ui.xpUnit||'XP')+'</div>'+
    '<div style="display:flex;gap:12px;justify-content:center">'+
    '<button class="mg-btn" id="mg-retry-btn" style="pointer-events:auto;font-size:13px;padding:10px 24px;border-color:'+(th.accent||'#ff6a9a')+';border-radius:14px">↺ '+(_ui.retry||'Retry')+'</button>'+
    '<button class="mg-btn" id="mg-continue-btn" style="pointer-events:auto;font-size:13px;padding:10px 24px;border-color:'+(th.success||'#90e0a0')+';color:'+(th.success||'#90e0a0')+';border-radius:14px">'+(_ui.continue||'Continue →')+'</button>'+
    '</div></div>';
  Audio.playSFX('complete');
  document.getElementById('mg-retry-btn').onclick=function(){_retryMiniGame()};
  document.getElementById('mg-continue-btn').onclick=function(){_advanceMiniGame(finalScore,xpGained,stars)};
}

function _retryMiniGame(){
  _minigameClosing=false;_mgScore=0;
  if(_lastMiniGameType){launchMiniGame(_lastMiniGameType)}
  else{_advanceMiniGame(0,0,0)}
}

function _advanceMiniGame(finalScore,xpGained,stars){
  _minigameClosing=false;
  const ov=document.getElementById('mini-game-overlay');
  if(ov){
    if(_mgIsFullscreen){ov.style.position='';ov.style.width='';ov.style.height='';ov.style.zIndex='';_mgIsFullscreen=false;}
    ov.style.display='none';ov.innerHTML='';
  }
  _addXP(xpGained);
  _updateChapterStars(currentChapter,stars);
  chapterComplete[currentChapter]=true;updateChapterBar();
  Audio.fadeOutBGM(300);setTimeout(function(){Audio.playBGM('dialog')},400);
  _showScoreFeedback(finalScore,xpGained,stars);
  gameState='playing';scriptIndex++;
  for(let i=scriptIndex-1;i>=0;i--)if(SCRIPT[i].type==='bg'){renderCharacters(SCRIPT[i].chars);break}
  _scheduleProcess(1800);
}

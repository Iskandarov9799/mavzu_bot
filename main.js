const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); tg.disableClosingConfirmation?.(); }

let questions=[], answers=[], current=0, score=0, answered=false, meta={}, resultSent=false;
const DEMO=[{id:1,t:"Demo savol",a:"A",b:"B",c:"C",d:"D",ok:"A",img:"",type:"choice"}];

async function loadQuestionsFromHash(){
  showLoader(true);
  const hash=new URLSearchParams(window.location.search).get('data')||window.location.hash.slice(1);
  if(!hash){questions=DEMO;meta={};initTest();showLoader(false);return;}
  try{
    const b64=hash.replace(/-/g,'+').replace(/_/g,'/');
    const binary=atob(b64);
    const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
    let jsonText;
    if(typeof DecompressionStream!=='undefined'){
      const ds=new DecompressionStream('deflate');
      const writer=ds.writable.getWriter();
      const reader=ds.readable.getReader();
      writer.write(bytes);writer.close();
      const chunks=[];
      while(true){const{done,value}=await reader.read();if(done)break;chunks.push(value);}
      const total=chunks.reduce((s,c)=>s+c.length,0);
      const out=new Uint8Array(total);let off=0;
      for(const c of chunks){out.set(c,off);off+=c.length;}
      jsonText=new TextDecoder('utf-8').decode(out);
    }else{jsonText=decodeURIComponent(escape(binary));}
    const parsed=JSON.parse(jsonText);
    questions=Array.isArray(parsed)?parsed:(parsed.questions||parsed);
    meta=Array.isArray(parsed)?{}:(parsed.meta||{});
    initTest();
  }catch(e){console.error(e);questions=DEMO;meta={};initTest();}
  showLoader(false);
}

function showLoader(on){const el=document.getElementById('loader');if(el)el.style.display=on?'flex':'none';}

function initTest(){
  if(!questions.length){showLoader(false);return;}
  answers=new Array(questions.length).fill(null);
  score=0;current=0;resultSent=false;
  const SUBJ={onatili:'📚 Ona tili',adabiyot:'📖 Adabiyot'};
  const titleEl=document.getElementById('header-title')||document.getElementById('hdr-title');
  if(titleEl)titleEl.textContent=SUBJ[meta.subject]||'📚 Test';
  const subEl=document.getElementById('header-sub')||document.getElementById('hdr-sub');
  const bolimLbl=meta.bolim_label||(meta.bolim>0?meta.bolim+'-bo\'lim':'Aralash');
  if(subEl)subEl.textContent=bolimLbl;
  if(tg){tg.setHeaderColor?.('#0a0e1a');tg.setBackgroundColor?.('#0a0e1a');}
  buildGrid();renderQuestion(0);
  document.getElementById('test-screen').style.display='block';
  document.getElementById('result-screen').style.display='none';
}

function buildGrid(){
  const g=document.getElementById('grid');if(!g)return;g.innerHTML='';
  questions.forEach((q,i)=>{
    const btn=document.createElement('button');
    btn.className='grid-btn'+(i===0?' current':'');
    btn.id='gb-'+i;btn.textContent=i+1;
    btn.onclick=()=>jumpTo(i);g.appendChild(btn);
  });
}

function updateGrid(){
  questions.forEach((q,i)=>{
    const btn=document.getElementById('gb-'+i);if(!btn)return;
    btn.className='grid-btn';
    if(i===current)btn.classList.add('current');
    else if(answers[i]==='correct')btn.classList.add('g-correct');
    else if(answers[i]==='wrong')btn.classList.add('g-wrong');
    else if(answers[i]==='skip')btn.classList.add('g-skip');
  });
}

function jumpTo(i){if(answers[i]!==null&&answers[i]!=='skip')return;current=i;renderQuestion(i);}

function renderQuestion(i){
  answered=false;const q=questions[i];const total=questions.length;
  const pct=Math.round((i+1)/total*100);
  const fillEl=document.getElementById('progress-fill')||document.getElementById('prg-fill');
  if(fillEl)fillEl.style.width=pct+'%';
  const numEl=document.getElementById('progress-num')||document.getElementById('prg-label');
  if(numEl)numEl.textContent=(i+1)+' / '+total;
  const pctEl=document.getElementById('progress-pct')||document.getElementById('prg-pct');
  if(pctEl)pctEl.textContent=pct+'%';
  const scoreEl=document.getElementById('score-badge')||document.getElementById('hdr-score');
  if(scoreEl)scoreEl.textContent=score+' ball';
  const badgeEl=document.getElementById('question-badge')||document.getElementById('qnum');
  if(badgeEl)badgeEl.textContent='SAVOL '+(i+1);
  const textEl=document.getElementById('question-text')||document.getElementById('qtxt');
  if(textEl){const raw=(q.t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');textEl.innerHTML=raw.replace(/\n/g,'<br>');}
  const imgEl=document.getElementById('question-img')||document.getElementById('qimg');
  if(imgEl){const imgSrc=q.img||'';imgEl.style.display=imgSrc?'block':'none';if(imgSrc)imgEl.src=imgSrc;}
  const fb=document.getElementById('feedback')||document.getElementById('fb');
  if(fb){fb.className='feedback';fb.style.display='none';fb.innerHTML='';}
  const btnSkip=document.getElementById('btn-skip');
  const btnNext=document.getElementById('btn-next');
  const btnFinish=document.getElementById('btn-finish');
  if(btnSkip)btnSkip.style.display='inline-flex';
  if(btnNext)btnNext.style.display='none';
  if(btnFinish)btnFinish.style.display='none';
  renderChoiceQuestion(q);updateGrid();
}

function renderChoiceQuestion(q){
  const opts=document.getElementById('options')||document.getElementById('opts');
  if(!opts)return;opts.innerHTML='';opts.style.display='flex';
  const LBLS=['A','B','C','D'];const TEXTS=[q.a||'',q.b||'',q.c||'',q.d||''];
  LBLS.forEach((lbl,idx)=>{
    if(!TEXTS[idx])return;
    const div=document.createElement('div');div.className='option';div.id='opt-'+lbl;
    div.innerHTML='<span class="option-letter">'+lbl+'</span><span class="option-text">'+TEXTS[idx]+'</span>';
    div.onclick=()=>selectOption(lbl);opts.appendChild(div);
  });
}

function selectOption(label){
  if(answered)return;answered=true;
  const q=questions[current];const correct=q.ok||q.correct_answer||'';const isOk=label===correct;
  document.querySelectorAll('.option').forEach(o=>{o.classList.add('disabled');o.onclick=null;});
  document.getElementById('opt-'+label)?.classList.add(isOk?'correct':'wrong');
  if(!isOk)document.getElementById('opt-'+correct)?.classList.add('show-correct');
  answers[current]=isOk?'correct':'wrong';
  if(isOk)score++;
  const scoreEl=document.getElementById('score-badge')||document.getElementById('hdr-score');
  if(scoreEl)scoreEl.textContent=score+' ball';
  const TEXTS={A:q.a,B:q.b,C:q.c,D:q.d};
  const fb=document.getElementById('feedback')||document.getElementById('fb');
  const solUrl=meta.solution_url||'';const qid=q.id||'';
  const linkHtml=solUrl?'<br><a href="'+solUrl+'" target="_blank" style="color:inherit;font-size:12px;text-decoration:underline;">📹 Yechimni ko\'rish (ID: '+qid+')</a>':'';
  if(fb){
    fb.style.display='flex';fb.className=isOk?'feedback correct-fb':'feedback wrong-fb';
    fb.innerHTML=isOk?'✅ To\'g\'ri javob!'+linkHtml:'❌ Noto\'g\'ri! To\'g\'ri: <b>'+correct+') '+(TEXTS[correct]||'')+'</b>'+linkHtml;
  }
  const btnSkip=document.getElementById('btn-skip');if(btnSkip)btnSkip.style.display='none';
  checkAllDone();updateGrid();
  tg?.HapticFeedback?.impactOccurred(isOk?'medium':'heavy');
}

function checkAllDone(){
  const noUnanswered=answers.every(a=>a!==null);
  const noSkipped=!answers.some(a=>a==='skip');
  const btnNext=document.getElementById('btn-next');
  const btnFinish=document.getElementById('btn-finish');
  if(noUnanswered&&noSkipped){if(btnNext)btnNext.style.display='none';if(btnFinish)btnFinish.style.display='inline-flex';}
  else{if(btnNext)btnNext.style.display='inline-flex';if(btnFinish)btnFinish.style.display='none';}
}

function skipQuestion(){
  answers[current]='skip';updateGrid();
  for(let i=current+1;i<questions.length;i++){if(answers[i]===null){current=i;renderQuestion(i);return;}}
  for(let i=0;i<current;i++){if(answers[i]===null){current=i;renderQuestion(i);return;}}
  showResult();
}

function nextQuestion(){
  for(let i=current+1;i<questions.length;i++){if(answers[i]===null){current=i;renderQuestion(i);return;}}
  for(let i=0;i<=current;i++){if(answers[i]===null){current=i;renderQuestion(i);return;}}
  showResult();
}

function showResult(){
  const total=questions.length;let correct=0,wrong=0,skip=0;
  answers.forEach((a,i)=>{
    if(a==='correct')correct++;
    else if(a==='wrong')wrong++;
    else if(a==='skip'||a===null){skip++;wrong++;}
  });
  const wrongOnly=wrong-skip;const pct=total>0?Math.round(correct/total*100):0;
  document.getElementById('test-screen').style.display='none';
  document.getElementById('result-screen').style.display='flex';
  let emoji,grade;
  if(pct>=86){emoji='🏆';grade='A\'lo (70% ustama)';}
  else if(pct>=80){emoji='🥇';grade='Oliy toifa';}
  else if(pct>=70){emoji='🥈';grade='1-toifa';}
  else if(pct>=60){emoji='🥉';grade='2-toifa';}
  else{emoji='📋';grade='Mutaxassis';}
  const userEl=document.getElementById('result-user');
  if(userEl){const u=tg?.initDataUnsafe?.user;if(u)userEl.textContent='👤 '+[u.first_name,u.last_name].filter(Boolean).join(' ');}
  const emojiEl=document.getElementById('result-emoji')||document.getElementById('r-emoji');
  const gradeEl=document.getElementById('result-grade')||document.getElementById('r-grade');
  const scoreEl=document.getElementById('result-score')||document.getElementById('r-score');
  const corrEl=document.getElementById('stat-correct')||document.getElementById('r-correct');
  const wrongEl=document.getElementById('stat-wrong')||document.getElementById('r-wrong');
  const skipEl=document.getElementById('stat-skip')||document.getElementById('r-skip');
  if(emojiEl)emojiEl.textContent=emoji;if(gradeEl)gradeEl.textContent=grade;
  if(scoreEl)scoreEl.textContent=pct+'%';if(corrEl)corrEl.textContent=correct;
  if(wrongEl)wrongEl.textContent=wrongOnly;if(skipEl)skipEl.textContent=skip;
  tg?.HapticFeedback?.notificationOccurred('success');
  if(!resultSent){
    resultSent=true;
    const wrongIds=[],correctIds=[];
    answers.forEach((a,i)=>{const qid=questions[i]?.id;if(!qid)return;if(a==='wrong'||a==='skip'||a===null)wrongIds.push(qid);else if(a==='correct')correctIds.push(qid);});
    const payload={
      correct,wrong:wrongOnly,skip,total,score:pct,
      subject:meta.subject||'onatili',bolim:meta.bolim||0,
      wrong_ids:wrongIds,correct_ids:correctIds,
    };
    if(tg&&typeof tg.sendData==='function'){try{tg.sendData(JSON.stringify(payload));}catch(e){console.error(e);}}
  }
}

function confirmFinish(){
  const un=answers.filter(a=>a===null).length;const sk=answers.filter(a=>a==='skip').length;
  if(un>0||sk>0){const msg=[];if(un>0)msg.push(un+' ta javobsiz');if(sk>0)msg.push(sk+' ta o\'tkazilgan');if(!confirm('⚠️ '+msg.join(', ')+' savol bor.\nBari-bir yakunlaysizmi?'))return;}
  showResult();
}
function closeApp(){if(tg)tg.close();}

window.skipQuestion=skipQuestion;window.nextQuestion=nextQuestion;
window.showResult=showResult;window.confirmFinish=confirmFinish;window.closeApp=closeApp;

loadQuestionsFromHash();

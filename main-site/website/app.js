'use strict';
const copy=window.SITE_COPY,menu=document.getElementById('menuToggle'),nav=document.getElementById('navigation');
function closeMenu(){menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label',copy.menuOpen);nav.classList.remove('is-open');}
menu.onclick=()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?copy.menuClose:copy.menuOpen);nav.classList.toggle('is-open',open);};
nav.querySelectorAll('a').forEach(a=>a.onclick=closeMenu);
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
const locale=document.getElementById('localeSelect');locale.onchange=()=>{const root=new URL(copy.language==='en'?'./':'../',location.href),paths={'en':'','zh-Hans':'zh-hans/'};const next=new URL(paths[locale.value],root);next.hash=location.hash;location.assign(next.href);};
const tabs=[...document.querySelectorAll('[role=tab]')];
function selectTab(tab){tabs.forEach(t=>{const active=t===tab;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1;document.getElementById(t.getAttribute('aria-controls')).hidden=!active;});}
tabs.forEach((t,i)=>{t.onclick=()=>selectTab(t);t.onkeydown=e=>{let idx;if(['ArrowLeft','ArrowRight'].includes(e.key))idx=(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;else if(e.key==='Home')idx=0;else if(e.key==='End')idx=tabs.length-1;if(idx!==undefined){e.preventDefault();selectTab(tabs[idx]);tabs[idx].focus();}};});
for(const [button,id]of [['productOpen','productDialog'],['noticeOpen','noticeDialog']])document.getElementById(button).onclick=()=>document.getElementById(id).showModal();
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.close).close());
document.querySelectorAll('dialog').forEach(d=>d.onclick=e=>{if(e.target!==d)return;const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();});
const contactForm=document.getElementById('contactForm');
let submissionId=null;
contactForm.addEventListener('input',()=>{submissionId=null;});
contactForm.onsubmit=async e=>{
 e.preventDefault();if(!contactForm.reportValidity())return;
 const get=id=>document.getElementById(id).value.trim(),status=document.getElementById('formStatus'),button=contactForm.querySelector('[type=submit]');
 if(!get('contactName')||!get('contactMessage')){status.textContent=copy.validation;status.hidden=false;return;}
 if(button.disabled)return;
 submissionId=submissionId||(crypto.randomUUID?crypto.randomUUID():'10000000-1000-4000-8000-100000000000'.replace(/[018]/g,c=>(Number(c)^(crypto.getRandomValues(new Uint8Array(1))[0]&(15>>(Number(c)/4)))).toString(16)));
 const payload={id:submissionId,name:get('contactName'),email:get('contactEmail'),investorType:get('contactType'),topic:get('contactTopic'),size:get('contactSize'),message:get('contactMessage'),language:copy.language};
 const original=button.innerHTML;button.disabled=true;button.textContent=copy.submitting;status.hidden=true;
 try{
  const response=await fetch('/api/applications',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(15000)});
  const result=await response.json();
  if(!response.ok||result.ok!==true)throw new Error('submission_failed');
  contactForm.reset();submissionId=null;document.getElementById('applicationDialog').showModal();
 }catch{status.textContent=copy.submitError;status.hidden=false;}
 finally{button.disabled=false;button.innerHTML=original;}
};


// Each slide contains its own image and copy, so both always transition together.
const hero=document.getElementById('heroCarousel');
if(hero){
 const slides=[...hero.querySelectorAll('.hero-slide')],dots=[...hero.querySelectorAll('[data-slide]')],pause=document.getElementById('heroPause');
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');let current=0,timer=null,paused=reduced.matches,hovered=false,focused=false,touchStart=null;
 function refreshTimer(){clearInterval(timer);timer=null;if(!paused&&!hovered&&!focused&&!document.hidden)timer=setInterval(()=>show(current+1),10000);}
 function show(index){current=(index+slides.length)%slides.length;slides.forEach((s,i)=>{const active=i===current;s.classList.toggle('is-active',active);s.setAttribute('aria-hidden',String(!active));s.inert=!active;});dots.forEach((d,i)=>{d.classList.toggle('is-active',i===current);d.setAttribute('aria-current',String(i===current));});document.getElementById('heroCount').textContent=String(current+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');}
 function updatePause(){pause.setAttribute('aria-label',paused?copy.play:copy.pause);pause.innerHTML=paused?'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 10 7-10 7Z"/></svg>':'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6v12M15 6v12"/></svg>';}
 function navigate(index){show(index);refreshTimer();}
 document.getElementById('heroPrevious').onclick=()=>navigate(current-1);
 document.getElementById('heroNext').onclick=()=>navigate(current+1);
 dots.forEach(d=>d.onclick=()=>navigate(Number(d.dataset.slide)));
 pause.onclick=()=>{paused=!paused;if(!paused){focused=false;hovered=false;}updatePause();refreshTimer();};
 hero.addEventListener('mouseenter',()=>{hovered=true;refreshTimer();});hero.addEventListener('mouseleave',()=>{hovered=false;refreshTimer();});
 hero.addEventListener('focusin',()=>{focused=true;refreshTimer();});hero.addEventListener('focusout',()=>{setTimeout(()=>{focused=hero.contains(document.activeElement);refreshTimer();},0);});
 document.addEventListener('visibilitychange',refreshTimer);
 hero.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'&&!e.target.closest('a,button'))touchStart={x:e.clientX,y:e.clientY};});
 hero.addEventListener('pointerup',e=>{if(!touchStart)return;const dx=e.clientX-touchStart.x,dy=e.clientY-touchStart.y;touchStart=null;if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)*1.5)navigate(current+(dx<0?1:-1));});hero.addEventListener('pointercancel',()=>{touchStart=null;});
 reduced.addEventListener('change',e=>{if(e.matches){paused=true;updatePause();refreshTimer();}});
 updatePause();refreshTimer();
}

const partnerShowcase=document.querySelector('.partner-showcase');
if(partnerShowcase){
 const frames=[...partnerShowcase.querySelectorAll('.partner-slide')],dots=[...partnerShowcase.querySelectorAll('[data-partner]')],pause=document.getElementById('partnerPause'),reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 let selected=0,startTouch=null,timer=null,paused=reduced.matches,hovered=false,focused=false,visible=false;
 function updateTimer(){clearInterval(timer);timer=null;if(visible&&!paused&&!hovered&&!focused&&!document.hidden)timer=setInterval(()=>selectPartner(selected+1),10000);}
 function selectPartner(index,manual=false){selected=(index+frames.length)%frames.length;frames.forEach((el,i)=>{const active=i===selected;el.classList.toggle('is-active',active);el.setAttribute('aria-hidden',String(!active));el.inert=!active;});dots.forEach((d,i)=>d.setAttribute('aria-current',String(i===selected)));if(manual){document.getElementById('partnerStatus').textContent=frames[selected].querySelector('h3').textContent+' · '+(selected+1)+' / '+frames.length;updateTimer();}}
 function manual(index,e){selectPartner(index,true);if(e&&e.detail>0)e.currentTarget.blur();}
 partnerShowcase.querySelector('.partner-prev').onclick=e=>manual(selected-1,e);
 partnerShowcase.querySelector('.partner-next').onclick=e=>manual(selected+1,e);
 dots.forEach(d=>d.onclick=e=>manual(Number(d.dataset.partner),e));
 function pauseLabel(){pause.setAttribute('aria-label',paused?copy.play:copy.pause);pause.textContent=paused?'▷':'Ⅱ';}
 pause.onclick=()=>{paused=!paused;if(!paused){focused=false;hovered=false;}pauseLabel();updateTimer();};
 partnerShowcase.onkeydown=e=>{if(e.key==='ArrowRight'){e.preventDefault();manual(selected+1);}if(e.key==='ArrowLeft'){e.preventDefault();manual(selected-1);}};
 partnerShowcase.addEventListener('mouseenter',()=>{hovered=true;updateTimer();});partnerShowcase.addEventListener('mouseleave',()=>{hovered=false;updateTimer();});
 partnerShowcase.addEventListener('focusin',()=>{focused=true;updateTimer();});partnerShowcase.addEventListener('focusout',()=>setTimeout(()=>{focused=partnerShowcase.contains(document.activeElement);updateTimer();},0));
 document.addEventListener('visibilitychange',updateTimer);
 if('IntersectionObserver' in window){new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;updateTimer();},{threshold:.15}).observe(partnerShowcase);}else{visible=true;}
 reduced.addEventListener('change',e=>{if(e.matches){paused=true;pauseLabel();updateTimer();}});
 partnerShowcase.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'&&!e.target.closest('button'))startTouch={x:e.clientX,y:e.clientY};});
 partnerShowcase.addEventListener('pointerup',e=>{if(!startTouch)return;const dx=e.clientX-startTouch.x,dy=e.clientY-startTouch.y;startTouch=null;if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)*1.5)manual(selected+(dx<0?1:-1));});partnerShowcase.addEventListener('pointercancel',()=>{startTouch=null;});
 pauseLabel();updateTimer();
}

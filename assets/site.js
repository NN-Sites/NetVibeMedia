(function(){
  var d=document, root=d.documentElement, body=d.body;
  root.classList.add('js');
  var KEY='nvm_acc_v2';
  function store(get,val){try{return get?JSON.parse(localStorage.getItem(KEY)||'{}'):localStorage.setItem(KEY,JSON.stringify(val))}catch(e){return {}}}

  /* sticky header */
  var nav=d.getElementById('nav');
  function onScroll(){nav.classList.toggle('scrolled',window.scrollY>12)}
  onScroll();window.addEventListener('scroll',onScroll,{passive:true});

  /* mobile menu */
  var burger=d.getElementById('burger'), mobile=d.getElementById('mobile');
  function setMenu(open){burger.setAttribute('aria-expanded',open);burger.setAttribute('aria-label',open?'סגירת תפריט ניווט':'פתיחת תפריט ניווט');burger.firstElementChild.firstElementChild.setAttribute('href',open?'#i-close':'#i-menu');mobile.hidden=!open}
  burger.addEventListener('click',function(){setMenu(burger.getAttribute('aria-expanded')!=='true')});
  mobile.addEventListener('click',function(e){if(e.target.tagName==='A')setMenu(false)});

  /* reveal on scroll */
  var els=[].slice.call(d.querySelectorAll('.reveal'));
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{threshold:.12,rootMargin:'0px 0px -40px 0px'});
    els.forEach(function(el){io.observe(el)});
  }else{els.forEach(function(el){el.classList.add('in')})}

  /* preselect service */
  var sel=d.getElementById('f-service');
  d.querySelectorAll('[data-service]').forEach(function(a){a.addEventListener('click',function(){if(sel)sel.value=a.getAttribute('data-service')})});
  d.getElementById('year').textContent=new Date().getFullYear();

  /* mobile-first sticky call-to-action (hidden on desktop by CSS, and while the contact form is on screen) */
  var cta=d.createElement('div');cta.className='m-cta';
  cta.innerHTML='<a class="btn btn-primary" href="./#contact">קבלו הצעה בחינם</a>';
  d.body.appendChild(cta);
  var contactSec=d.getElementById('contact');
  if(contactSec&&'IntersectionObserver' in window){new IntersectionObserver(function(es){cta.classList.toggle('off',es[0].isIntersecting)}).observe(contactSec)}
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&burger.getAttribute('aria-expanded')==='true'){setMenu(false);burger.focus()}});

  /* ---------- accessibility widget ---------- */
  var btn=d.getElementById('acc-btn'), panel=d.getElementById('acc-panel'), closeBtn=d.getElementById('acc-close');
  var st=store(true); st.fs=st.fs||0; st.cls=st.cls||[];
  var fsNames=['רגיל','גדול','גדול מאוד','ענק'];
  function applyAll(){
    ['acc-fs-1','acc-fs-2','acc-fs-3'].forEach(function(c){root.classList.remove(c)});
    if(st.fs>0)root.classList.add('acc-fs-'+st.fs);
    d.getElementById('fs-label').textContent='גודל טקסט: '+fsNames[st.fs];
    panel.querySelectorAll('.acc-opt[data-cls]').forEach(function(b){
      var on=st.cls.indexOf(b.dataset.cls)>-1;
      body.classList.toggle(b.dataset.cls,on);b.setAttribute('aria-pressed',on);
    });
    store(false,st);
  }
  applyAll();
  function openPanel(o){panel.hidden=!o;btn.setAttribute('aria-expanded',o);if(o){closeBtn.focus()}else{btn.focus()}}
  btn.addEventListener('click',function(){openPanel(panel.hidden)});
  closeBtn.addEventListener('click',function(){openPanel(false)});
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&!panel.hidden){openPanel(false)}});
  panel.querySelectorAll('.acc-opt[data-cls]').forEach(function(b){b.addEventListener('click',function(){
    var i=st.cls.indexOf(b.dataset.cls);if(i>-1)st.cls.splice(i,1);else st.cls.push(b.dataset.cls);applyAll();
  })});
  d.getElementById('fs-inc').addEventListener('click',function(){st.fs=Math.min(3,st.fs+1);applyAll()});
  d.getElementById('fs-dec').addEventListener('click',function(){st.fs=Math.max(0,st.fs-1);applyAll()});
  d.getElementById('acc-reset').addEventListener('click',function(){st.fs=0;st.cls=[];applyAll()});

  /* ---------- contact form (Firebase loaded on demand) ---------- */
  /* ---------- works / logos (assets/works.json) ---------- */
  var worksReq=null;
  function loadWorks(){if(!worksReq){worksReq=fetch('assets/works.json',{cache:'no-cache'}).then(function(r){return r.ok?r.json():{}}).catch(function(){return {}})}return worksReq}
  function el(tag,cls,html){var e=d.createElement(tag);if(cls)e.className=cls;if(html!=null)e.textContent=html;return e}
  var track=d.getElementById('logo-track');
  if(track){
    loadWorks().then(function(w){
      var logos=(w.logos||[]).filter(function(x){return x&&x.file});
      var items=[];
      if(logos.length){
        var base=logos.slice();while(base.length<8)base=base.concat(logos);
        base.forEach(function(l){var img=el('img','logo-img');img.src='client-logos/'+l.file;img.alt=l.name||'';img.height=48;img.loading='lazy';img.decoding='async';items.push(img)});
      }else{
        for(var i=0;i<8;i++)items.push(el('span','logo-ph','העסק שלך כאן'));
        var note=d.getElementById('logos-note');if(note)note.hidden=false;
      }
      function fill(parent,hidden){items.forEach(function(n){var c=n.cloneNode(true);parent.appendChild(c)});if(hidden)parent.setAttribute('aria-hidden','true')}
      var a=el('div','logo-set'),b=el('div','logo-set');fill(a,false);fill(b,true);
      if(!logos.length){a.setAttribute('aria-hidden','true')}
      track.appendChild(a);track.appendChild(b);
    });
  }
  var gal=d.querySelectorAll('[data-gallery]');
  gal.forEach(function(box){
    var kind=box.getAttribute('data-gallery');
    loadWorks().then(function(w){
      var list=(w[kind]||[]).filter(function(x){return x&&x.file||x&&x.url});
      if(!list.length){box.appendChild(el('p','works-empty','העבודות יעלו לכאן בקרוב. רוצים לראות דוגמאות מתאימות לעסק שלכם? השאירו פרטים ונשלח.'));return}
      list.forEach(function(it){
        var card=el('article','work');
        if(kind==='videos'){
          var v=d.createElement('video');v.controls=true;v.preload='metadata';v.playsInline=true;v.src='commercial-videos/'+it.file;
          if(it.poster)v.poster='commercial-videos/'+it.poster;
          v.setAttribute('aria-label',it.title||'סרטון פרסומת');card.appendChild(v);
        }else{
          var folder={sites:'websites-landing/',cards:'business-cards/',brand:'logo-design/'}[kind]||'business-cards/';
          var img=el('img');img.src=folder+(it.image||it.file);img.alt=it.title||'';img.loading='lazy';img.decoding='async';
          if(kind==='sites'&&it.url){var a=d.createElement('a');a.href=it.url;a.target='_blank';a.rel='noopener';a.appendChild(img);card.appendChild(a)}else card.appendChild(img);
        }
        var body=el('div','work-body');
        if(it.title)body.appendChild(el('h3',null,it.title));
        if(it.desc)body.appendChild(el('p',null,it.desc));
        if(kind==='sites'&&it.url){var l=el('a','work-link','לצפייה באתר');l.href=it.url;l.target='_blank';l.rel='noopener';body.appendChild(l)}
        card.appendChild(body);box.appendChild(card);
      });
    });
  });

  var form=d.getElementById('order-form'), statusEl=d.getElementById('form-status'), submitBtn=d.getElementById('submit-btn');
  var nameI=d.getElementById('f-name'), phoneI=d.getElementById('f-phone');
  var FB={apiKey:"AIzaSyBYrdNSkWx8gUzkTyIMuIEKWMFfyU4ZuNs",authDomain:"netvibe-media.firebaseapp.com",projectId:"netvibe-media",storageBucket:"netvibe-media.firebasestorage.app",messagingSenderId:"345459958522",appId:"1:345459958522:web:5a7c1ee5517d8e60499f43",measurementId:"G-VQL10G9K24"};
  var SERVICES={landing:'דף נחיתה',website:'אתר תדמית',video1:'סרטון פרסומת',video2:'2 סרטוני פרסומת',card:'כרטיס ביקור',other:'לא בטוח'};
  var fbPromise=null;
  function loadFirebase(){
    if(!fbPromise){fbPromise=Promise.all([
      import('https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js'),
      import('https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js')
    ]).then(function(m){var app=m[0].initializeApp(FB);return {db:m[1].getFirestore(app),fs:m[1]}})}
    return fbPromise;
  }
  if(!form)return;
  try{var qs=new URLSearchParams(location.search).get('service');if(qs&&sel)sel.value=qs}catch(e){}
  form.addEventListener('focusin',function(){loadFirebase().catch(function(){fbPromise=null})},{once:true});

  function setErr(input,id,msg){var el=d.getElementById(id);el.textContent=msg||'';if(msg){input.setAttribute('aria-invalid','true')}else{input.removeAttribute('aria-invalid')}}
  function setStatus(type,msg){statusEl.className='status '+(type||'');statusEl.textContent=msg||''}

  form.addEventListener('submit',function(e){
    e.preventDefault();
    setStatus('');
    if(d.getElementById('f-website').value){return}
    var name=nameI.value.trim(), phone=phoneI.value.trim(), digits=phone.replace(/\D/g,'');
    var bad=null;
    if(name.length<2){setErr(nameI,'e-name','נא להזין שם מלא');bad=bad||nameI}else setErr(nameI,'e-name','');
    if(digits.length<9||digits.length>13){setErr(phoneI,'e-phone','נא להזין מספר טלפון תקין');bad=bad||phoneI}else setErr(phoneI,'e-phone','');
    if(bad){bad.focus();return}

    var service=sel.value, message=d.getElementById('f-msg').value.trim();
    submitBtn.disabled=true;submitBtn.textContent='שולח...';
    loadFirebase().then(function(f){
      var col=f.fs.collection(f.db,'orders');
      var base={name:name,phone:phone,createdAt:f.fs.serverTimestamp(),status:'new'};
      var full=Object.assign({},base,{service:service||'',serviceLabel:SERVICES[service]||'',message:message,source:'website'});
      return f.fs.addDoc(col,full).catch(function(){
        /* fallback to the minimal legacy document shape */
        var extra=[SERVICES[service],message].filter(Boolean).join(' | ');
        return f.fs.addDoc(col,Object.assign({},base,{name:extra?name+' ['+extra+']':name}));
      });
    }).then(function(){
      form.reset();
      setStatus('ok','תודה! הפרטים התקבלו בהצלחה. נחזור אליכם בהקדם.');
    }).catch(function(){
      fbPromise=null;
      setStatus('bad','אירעה שגיאה בשליחה. נסו שוב בעוד רגע.');
    }).then(function(){
      submitBtn.disabled=false;submitBtn.textContent='שלחו לי הצעה';
    });
  });
})();

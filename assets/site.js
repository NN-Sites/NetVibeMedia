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

  /* ---------- WhatsApp orders (everything except websites / landing pages) ---------- */
  var WA='972533752747';
  var WA_SERVICES={
    landing:{label:'דף נחיתה',intent:'בדף נחיתה',price:'500 ₪ לחודש'},
    website:{label:'אתר תדמית',intent:'באתר תדמית',price:'700 ₪ לחודש'},
    other:{label:'',intent:'בשירותים שלכם',price:''},
    video1:{label:'סרטון פרסומת',intent:'ביצירת סרטון פרסומת',price:'250 ₪ (מבצע, במקום 500 ₪)'},
    video2:{label:'2 סרטוני פרסומת',intent:'ביצירת 2 סרטוני פרסומת',price:'400 ₪'},
    card:{label:'כרטיס ביקור',intent:'בעיצוב כרטיס ביקור',price:'50 ₪'},
    logo:{label:'עיצוב לוגו',intent:'בעיצוב לוגו',price:'30 ₪'},
    logoanim:{label:'לוגו עם אנימציה',intent:'בעיצוב לוגו עם אנימציה',price:'50 ₪ (30 ₪ לוגו + 20 ₪ אנימציה)'}
  };
  function waLink(key,info){
    var sv=WA_SERVICES[key];if(!sv)return null;
    info=info||{};
    var NL=String.fromCharCode(10);
    var L=['היי, אני מתעניין '+sv.intent+' 🙂','',
      (sv.price?'ראיתי באתר ש'+sv.label+' עולה *'+sv.price+'*, ואשמח לשמוע עוד פרטים, לתאם ולהתחיל.':'ראיתי את האתר ואשמח לשמוע עוד על השירותים והמחירים.')];
    var det=[];
    if(info.name)det.push('👤 *שם:* '+info.name);
    if(info.phone)det.push('📞 *טלפון:* '+info.phone);
    if(info.message)det.push('📝 *על העסק / מה חשוב לי:* '+info.message);
    if(det.length){L.push('');L=L.concat(det)}
    L.push('');
    L.push(info.name?'תודה רבה, אשמח שתחזרו אליי 🙏':'אשמח שתחזרו אליי, תודה! 🙏');
    return 'https://wa.me/'+WA+'?text='+encodeURIComponent(L.join(NL));
  }
  d.querySelectorAll('a[data-service],a[href*="service="]').forEach(function(a){
    var key=a.getAttribute('data-service');
    if(!key){var m=/[?&]service=([a-z0-9]+)/.exec(a.getAttribute('href')||'');key=m&&m[1]}
    var url=key&&waLink(key);
    if(url){a.href=url;a.target='_blank';a.rel='noopener';a.removeAttribute('data-service')}
  });

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
  function getJSON(u){return fetch(u,{cache:'no-cache'}).then(function(r){return r.ok?r.json():null}).catch(function(){return null})}
  function stem(f){return f.replace(/\.[^.]+$/,'')}
  function clean(f){return stem(f).replace(/[-_]+/g,' ').trim()}
  /* every file found in a media folder (assets/manifest.json, built automatically) is shown;
     assets/works.json is optional and only adds titles/descriptions/links or custom ordering */
  function loadWorks(){
    if(!worksReq){worksReq=Promise.all([getJSON('assets/manifest.json'),getJSON('assets/works.json')]).then(function(r){
      var man=r[0]||{},meta=r[1]||{},out={};
      ['videos','sites','apps','cards','brand','logos'].forEach(function(k){
        var files=man[k],res=[],seen={};
        (meta[k]||[]).forEach(function(m){
          var f=m.file||m.image;if(!f)return;
          if(files&&files.indexOf(f)<0&&!m.url)return;
          var o={};for(var p in m)o[p]=m[p];o.file=f;if((k==='sites'||k==='apps')&&!o.image)o.image=f;
          if(k==='videos'&&!o.poster&&man.videoPosters&&man.videoPosters[f])o.poster=man.videoPosters[f];
          res.push(o);seen[f]=1;
        });
        (files||[]).forEach(function(f){
          if(seen[f])return;
          var o={file:f};
          if(k==='sites'||k==='apps')o.image=f;
          if(k==='videos'&&man.videoPosters&&man.videoPosters[f])o.poster=man.videoPosters[f];
          if(k==='logos')o.name=clean(f);
          res.push(o);
        });
        out[k]=res;
      });
      out.previews=man.videoPreviews||[];
      return out;
    })}
    return worksReq;
  }
  function el(tag,cls,html){var e=d.createElement(tag);if(cls)e.className=cls;if(html!=null)e.textContent=html;return e}
  var track=d.getElementById('logo-track');
  if(track){
    loadWorks().then(function(w){
      var logos=(w.logos||[]).filter(function(x){return x&&x.file});
      if(!logos.length)return;
      var sec=d.getElementById('clients');if(sec)sec.hidden=false;
      d.querySelectorAll('a[href="#clients"]').forEach(function(a){if(a.parentNode)a.parentNode.hidden=false});
      /* each half of the track must be wider than the screen, so the loop has no gaps */
      var wide=Math.max(window.innerWidth,(window.screen&&screen.width)||0,1280);
      var count=Math.max(logos.length,Math.ceil(wide/110)+1);
      for(var half=0;half<2;half++){
        var set=el('div','logo-set');
        for(var i=0;i<count;i++){
          var l=logos[i%logos.length],img=el('img','logo-img');
          var real=half===0&&i<logos.length;
          img.src='client-logos/'+encodeURIComponent(l.file);img.alt=real?(l.name||''):'';
          if(!real)img.setAttribute('aria-hidden','true');
          img.width=img.height=120;img.decoding='async';
          set.appendChild(img);
        }
        track.appendChild(set);
      }
      function setSpeed(){var s=track.firstChild.offsetWidth;if(s)track.style.animationDuration=(s/45)+'s'}
      setSpeed();window.addEventListener('resize',setSpeed);
    });
  }
  /* ---------- moving video gallery: rows of silent loops, click opens the full video ---------- */
  var REEL_ROWS=3, REEL_SPEED=38; /* number of rows, pixels per second */
  function vurl(f){return 'commercial-videos/'+encodeURIComponent(f)}
  function purl(f){return 'commercial-videos/previews/'+encodeURIComponent(f)}
  function buildReel(box,list,previews){
    var reduce=window.matchMedia?matchMedia('(prefers-reduced-motion: reduce)'):{matches:false};
    var userPaused=false, player=null, loops=[];
    box.className='reel';
    function still(){return userPaused||reduce.matches||d.body.classList.contains('acc-still')}
    /* a loop plays only while it is on screen and motion is allowed */
    function sync(v){
      var on=v._vis&&!still()&&!(player&&player.open)&&!d.hidden;
      if(on){
        if(!v.getAttribute('src'))v.src=v._loop;
        if(v.paused){var p=v.play();if(p&&p.catch)p.catch(function(){})}
      }else if(!v.paused)v.pause();
    }
    function syncAll(){loops.forEach(sync)}
    var io='IntersectionObserver' in window?new IntersectionObserver(function(es){
      es.forEach(function(x){x.target._vis=x.isIntersecting;sync(x.target)});
    }):null;

    function openPlayer(it){
      if(!player){
        player=el('dialog','reel-player');
        var x=el('button','reel-close','✕');x.type='button';x.setAttribute('aria-label','סגירת הסרטון');
        var full=d.createElement('video');full.controls=true;full.playsInline=true;full.setAttribute('playsinline','');full.setAttribute('controlslist','nodownload');
        player.appendChild(x);player.appendChild(full);player.appendChild(el('div','reel-caption'));
        x.addEventListener('click',function(){player.close()});
        player.addEventListener('click',function(e){if(e.target===player)player.close()});
        player.addEventListener('close',function(){full.pause();full.removeAttribute('src');full.load();syncAll()});
        d.body.appendChild(player);
      }
      if(!player.showModal){window.location.href=vurl(it.file);return}
      var v=player.querySelector('video'),cap=player.querySelector('.reel-caption');
      cap.textContent='';
      if(it.title)cap.appendChild(el('h3',null,it.title));
      if(it.desc)cap.appendChild(el('p',null,it.desc));
      v.setAttribute('aria-label',it.title||'סרטון פרסומת');
      v.src=vurl(it.file);
      player.showModal();syncAll();
      var p=v.play();if(p&&p.catch)p.catch(function(){});
    }

    function tile(it,real){
      var b=el('button','reel-tile'),v=d.createElement('video');
      b.type='button';
      b.setAttribute('aria-label','צפייה בסרטון: '+(it.title||clean(it.file)));
      if(!real){b.tabIndex=-1;b.setAttribute('aria-hidden','true')}
      v.muted=true;v.defaultMuted=true;v.loop=true;v.playsInline=true;v.setAttribute('playsinline','');v.setAttribute('muted','');
      v.tabIndex=-1;v.setAttribute('aria-hidden','true');v.disablePictureInPicture=true;
      if(previews.indexOf(it.file)>-1){
        v.preload='none';v.poster=purl(it.file+'.jpg');v._loop=purl(it.file+'.mp4');
        loops.push(v);if(io)io.observe(v);
      }else{ /* no preview yet: show a still frame of the original */
        v.preload='metadata';v.src=vurl(it.file)+'#t=1';
        if(it.poster)v.poster=vurl(it.poster);
      }
      b.appendChild(v);b.appendChild(el('span','reel-play'));
      b.addEventListener('click',function(){openPlayer(it)});
      return b;
    }

    /* each half of a row must be at least as wide as the screen, so the loop has no gaps */
    var wide=Math.max(window.innerWidth,(window.screen&&screen.width)||0,1280);
    var perSet=Math.max(list.length,Math.ceil(wide/110)+1);
    var tracks=[];
    for(var r=0;r<REEL_ROWS;r++){
      var row=el('div','reel-row'),track=el('div','reel-track '+(r%2?'to-left':'to-right'));
      var shift=Math.round(r*list.length/REEL_ROWS);
      for(var half=0;half<2;half++){
        var set=el('div','reel-set');
        for(var i=0;i<perSet;i++)set.appendChild(tile(list[(i+shift)%list.length],r===0&&half===0&&i<list.length));
        track.appendChild(set);
      }
      row.appendChild(track);box.appendChild(row);tracks.push(track);
    }

    var toggle=el('button','reel-toggle','עצירת התנועה');toggle.type='button';
    toggle.addEventListener('click',function(){
      userPaused=!userPaused;
      box.classList.toggle('is-paused',userPaused);
      toggle.textContent=userPaused?'המשך תנועה':'עצירת התנועה';
      syncAll();
    });
    box.appendChild(toggle);

    /* the width is 0 while the section is filtered out, so measure again when it appears */
    function setSpeed(){tracks.forEach(function(t){var w=t.firstChild.offsetWidth;if(w)t.style.animationDuration=(w/REEL_SPEED)+'s'})}
    setSpeed();window.addEventListener('resize',setSpeed);
    if('ResizeObserver' in window)new ResizeObserver(setSpeed).observe(tracks[0].firstChild);
    if(!io){loops.forEach(function(v){v._vis=true});syncAll()}
    d.addEventListener('visibilitychange',syncAll);
    if(reduce.addEventListener)reduce.addEventListener('change',syncAll);
    if('MutationObserver' in window)new MutationObserver(syncAll).observe(d.body,{attributes:true,attributeFilter:['class']});
  }
  var gal=d.querySelectorAll('[data-gallery]');
  gal.forEach(function(box){
    var kind=box.getAttribute('data-gallery');
    loadWorks().then(function(w){
      var list=(w[kind]||[]).filter(function(x){return x&&x.file||x&&x.url});
      if(!list.length){box.appendChild(el('p','works-empty','העבודות יעלו לכאן בקרוב. רוצים לראות דוגמאות מתאימות לעסק שלכם? השאירו פרטים ונשלח.'));return}
      if(kind==='videos'){buildReel(box,list,w.previews||[]);return}
      list.forEach(function(it){
        var card=el('article','work');
        var folder={sites:'websites-landing/',apps:'apps-showcase/',cards:'business-cards/',brand:'logo-design/'}[kind]||'business-cards/';
        var img=el('img');img.src=folder+encodeURIComponent(it.image||it.file);img.alt=it.title||'';img.loading='lazy';img.decoding='async';
        if((kind==='sites'||kind==='apps')&&it.url){
          /* screenshot with a visit button inside its lower edge */
          var media=el('div','work-media'),l=el('a','work-visit',kind==='apps'?'לאתר האפליקציה':'לכניסה לאתר');
          l.href=it.url;l.target='_blank';l.rel='noopener';
          l.setAttribute('aria-label',l.textContent+(it.title?' – '+it.title:'')+' (נפתח בלשונית חדשה)');
          img.width=960;img.height=600;
          media.appendChild(img);media.appendChild(l);card.appendChild(media);
        }else card.appendChild(img);
        var body=el('div','work-body');
        if(it.title)body.appendChild(el('h3',null,it.title));
        if(it.desc)body.appendChild(el('p',null,it.desc));
        if(body.children.length)card.appendChild(body);box.appendChild(card);
      });
    });
  });

  /* ---------- portfolio filter (portfolio.html), linkable as #websites / #cards / #videos ---------- */
  var pf=d.querySelector('[data-portfolio]');
  if(pf){
    var pfBtns=[].slice.call(pf.querySelectorAll('[data-filter]')), pfSecs=[].slice.call(pf.querySelectorAll('[data-cat]'));
    var pfHas=function(c){return pfBtns.some(function(b){return b.dataset.filter===c})};
    var pfShow=function(c){
      pf.setAttribute('data-view',c);
      pfBtns.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.filter===c))});
      pfSecs.forEach(function(s){s.hidden=c!=='all'&&s.dataset.cat!==c});
    };
    var pfHash=function(){var c=location.hash.slice(1);if(pfHas(c))pfShow(c)};
    pfBtns.forEach(function(b){b.addEventListener('click',function(){
      var c=b.dataset.filter;pfShow(c);
      history.replaceState(null,'',c==='all'?location.pathname+location.search:'#'+c);
    })});
    window.addEventListener('hashchange',pfHash);pfHash();
  }

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
    var waUrl=waLink(service||'other',{name:name,phone:phone,message:message});
    if(waUrl){var w=window.open(waUrl,'_blank');if(!w){window.location.href=waUrl;}}
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

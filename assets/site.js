(function(){
  var root=document.documentElement;
  var b=document.querySelector('.theme');
  if(b)b.addEventListener('click',function(){
    var dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme=dark?'light':'dark';
    try{localStorage.setItem('theme',root.dataset.theme)}catch(e){}
  });
  document.querySelectorAll('.vid').forEach(function(v){
    v.addEventListener('click',function(){
      var f=document.createElement('iframe');
      f.src='https://www.youtube-nocookie.com/embed/'+v.dataset.id+'?autoplay=1&rel=0';
      f.allow='autoplay; encrypted-media; picture-in-picture';f.allowFullscreen=true;f.title='Demo video';
      v.textContent='';v.appendChild(f);v.style.cursor='default';
    },{once:true});
  });
  var q=document.getElementById('q'),grid=document.getElementById('grid');
  if(!q||!grid)return;
  var g='',cards=[].slice.call(grid.children),none=document.getElementById('none');
  function run(){
    var s=q.value.trim().toLowerCase(),n=0;
    cards.forEach(function(c){var ok=(!g||c.dataset.g===g)&&(!s||c.dataset.t.indexOf(s)>-1);c.hidden=!ok;if(ok)n++});
    if(none)none.hidden=n>0;
  }
  q.addEventListener('input',run);
  document.querySelectorAll('.chip').forEach(function(c){c.addEventListener('click',function(){
    document.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});c.classList.add('on');g=c.dataset.g;run();
  })});
})();

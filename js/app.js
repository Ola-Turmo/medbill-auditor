(function(){'use strict';
const h=document.querySelector('.hamburger'),hn=document.querySelector('.header-nav');
if(h&&hn)h.addEventListener('click',()=>{h.getAttribute('aria-expanded')!=='true';hn.classList.toggle('active')});
function initUZ(zId,iId){const z=document.getElementById(zId),i=document.getElementById(iId);if(!z||!i)return;
z.addEventListener('click',()=>i.click());z.addEventListener('dragover',e=>{e.preventDefault();z.classList.add('dragover')});
z.addEventListener('dragleave',()=>z.classList.remove('dragover'));
z.addEventListener('drop',e=>{e.preventDefault();z.classList.remove('dragover');if(e.dataTransfer.files.length>0){i.files=e.dataTransfer.files;hf(i.files[0],z)}});
i.addEventListener('change',()=>{if(i.files.length>0)hf(i.files[0],z)})}
function hf(f,z){const max=10*1024*1024;if(!f.name.match(/\.(pdf|jpg|jpeg|png)$/i))return show('Please upload PDF, JPG or PNG.','error');
if(f.size>max)return show('File too large (max 10MB).','error');
const pe=document.getElementById('upload-progress');if(pe)pe.style.display='block';
const fl=document.getElementById('progress-fill'),tx=document.getElementById('progress-text');
if(fl)fl.style.width='0%';if(tx)tx.textContent='Uploading...';
let p=0;const iv=setInterval(()=>{p+=Math.random()*15;if(p>90){clearInterval(iv);return}if(fl)fl.style.width=Math.min(p,90)+'%'},300);
const fd=new FormData();fd.append('file',f);const x=new XMLHttpRequest();x.open('POST','/api/upload',true);
x.upload.onprogress=function(e){if(e.lengthComputable&&fl)fl.style.width=Math.min((e.loaded/e.total)*100,90)+'%'};
x.onload=function(){clearInterval(iv);if(x.status===200){const r=JSON.parse(x.responseText);if(fl)fl.style.width='100%';if(tx)tx.textContent='Redirecting...';setTimeout(()=>window.location.href='/status?id='+encodeURIComponent(r.job_id),800)}else{show('Upload failed.','error');if(pe)pe.style.display='none'}};
x.onerror=function(){clearInterval(iv);show('Network error.','error')};x.send(fd)}
function show(m,t){const e=document.createElement('div');e.style.cssText=`position:fixed;bottom:24px;left:50%;transform:translateX(-50%);padding:14px 24px;border-radius:10px;font-size:14px;z-index:9999;max-width:480px;box-shadow:0 4px 20px rgba(0,0,0,.15);background:${t==='error'?'#fef2f2':'#f0fdf4'};color:${t==='error'?'#dc2626':'#16a34a'}`;e.textContent=m;document.body.appendChild(e);setTimeout(()=>e.remove(),4000)}

function initStatus(){const p=new URLSearchParams(window.location.search),id=p.get('id');if(!id)return;
const steps=document.querySelectorAll('.status-step');
function us(i,s){if(!steps[i])return;steps[i].classList.remove('active','completed');if(s==='active')steps[i].classList.add('active');if(s==='completed'){steps[i].classList.add('completed');const ic=steps[i].querySelector('.status-step-icon');if(ic)ic.textContent='✅'}}
async function poll(){try{const r=await fetch('/api/status/'+encodeURIComponent(id));if(!r.ok)return;const d=await r.json();
if(d.step>=1)us(0,'completed');if(d.step===1)us(0,'active');if(d.step>=2)us(1,'completed');if(d.step===2)us(1,'active');if(d.step>=3)us(2,'completed');if(d.step===3)us(2,'active');if(d.step>=4)us(3,'completed');if(d.step===4)us(3,'active');
if(d.status==='completed'){window.location.href='/report/'+encodeURIComponent(d.report_id||id);return}
setTimeout(poll,3000)}catch(e){setTimeout(poll,5000)}}
if(steps.length>0){us(0,'active');setTimeout(poll,2000)}}

document.querySelectorAll('.faq-item').forEach(i=>{i.addEventListener('toggle',function(){if(this.open)document.querySelectorAll('.faq-item[open]').forEach(o=>{if(o!==this)o.open=false})})});
document.querySelectorAll('a[href^="#"]').forEach(a=>{a.addEventListener('click',function(e){const t=document.querySelector(this.getAttribute('href'));if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth'})}})});
document.addEventListener('DOMContentLoaded',()=>{initUZ('hero-upload-zone','hero-file-input');initUZ('upload-zone-lg','file-input');const sp=document.getElementById('status-page');if(sp&&sp.style.display!=='none')initStatus()});
})();

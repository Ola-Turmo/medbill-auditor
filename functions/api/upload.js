// MedBill Auditor — API Worker (Cloudflare Pages Functions)
import { Router } from 'itty-router';
const router = Router();

function json(d, s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}
function uuid(){return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return(c==='x'?r:(r&0x3|0x8)).toString(16);})}

// POST /api/upload
router.post('/api/upload', async (req, env) => {
  try{
    const fd = await req.formData(), file = fd.get('file'), email = fd.get('email')||'';
    if(!file) return json({error:'No file'},400);
    const ext = (file.name||'bill.pdf').split('.').pop()?.toLowerCase();
    if(!['pdf','jpg','jpeg','png'].includes(ext)) return json({error:'Invalid type. PDF, JPG, PNG only.'},400);
    if(file.size > 10*1024*1024) return json({error:'File too large. Max 10MB.'},413);
    const jobId = uuid();
    const job = {id:jobId,status:'queued',step:0,email,fileName:file.name,fileType:ext,fileSize:file.size,plan:'free',createdAt:Date.now(),updatedAt:Date.now()};
    if(env.BILLS_BUCKET && file.arrayBuffer) await env.BILLS_BUCKET.put(`bills/${jobId}/${file.name}`, await file.arrayBuffer(), {httpMetadata:{contentType:file.type}});
    await env.MEDBILL_KV.put(`job:${jobId}`, JSON.stringify(job), {expirationTtl:86400*7});
    await env.MEDBILL_KV.put(`queue:${jobId}`, JSON.stringify(job), {expirationTtl:86400});
    if(email && env.AGENTMAIL_API_KEY) try{await sendEmail(email,'MedBill — Your bill is being analyzed',`Hi,\n\nWe received your bill and are analyzing it.\n\nCheck results: ${env.SITE_URL||'https://medbill.ai'}/status?id=${jobId}\n\n2-5 minutes.`,env);}catch(e){}
    return json({success:true,job_id:jobId,status_url:`/status?id=${jobId}`},201);
  }catch(e){return json({error:'Upload failed'},500);}
});

// GET /api/status/:id
router.get('/api/status/:id', async (req, env) => {
  try{
    const j = JSON.parse(await env.MEDBILL_KV.get(`job:${req.params.id}`)||'{}');
    if(!j.id) return json({error:'Not found'},404);
    return json({id:j.id,status:j.status,step:j.step||0,email:j.email||'',error_count:j.error_count||0,savings_estimate:j.savings_estimate||null,report_id:j.report_id||null,plan:j.plan||'free'});
  }catch(e){return json({error:'Failed'},500);}
});

// GET /api/report/:id
router.get('/api/report/:id', async (req, env) => {
  try{
    const id=req.params.id;
    let r=await env.MEDBILL_KV.get(`report:${id}`);
    if(r) return json(JSON.parse(r));
    const j=await env.MEDBILL_KV.get(`job:${id}`);
    if(!j) return json({error:'Not found'},404);
    const job=JSON.parse(j);
    if(job.status!=='completed') return json({error:'Not ready',status:job.status},202);
    return json({id,plan:job.plan||'free',billed_amount:job.billed_amount,service_count:job.service_count,error_count:job.error_count||0,findings:job.findings||[],dispute_letter:job.dispute_letter,phone_script:job.phone_script,rate_comparisons:job.rate_comparisons||[]});
  }catch(e){return json({error:'Failed'},500);}
});

// POST /api/report — Receive audit results from VPS
router.post('/api/report', async (req, env) => {
  try{
    const b=await req.json();
    if(!b.job_id) return json({error:'Missing job_id'},400);
    const js=await env.MEDBILL_KV.get(`job:${b.job_id}`);
    if(!js) return json({error:'Job not found'},404);
    const job=JSON.parse(js);
    Object.assign(job,{status:'completed',step:4,updatedAt:Date.now(),findings:b.findings||[],dispute_letter:b.dispute_letter,phone_script:b.phone_script,rate_comparisons:b.rate_comparisons||[],billed_amount:b.billed_amount,service_count:b.service_count,error_count:b.error_count||(b.findings?b.findings.length:0),savings_estimate:b.savings_estimate,report_id:b.job_id});
    await env.MEDBILL_KV.put(`report:${b.job_id}`, JSON.stringify(job), {expirationTtl:86400*30});
    await env.MEDBILL_KV.put(`job:${b.job_id}`, JSON.stringify(job));
    await env.MEDBILL_KV.delete(`queue:${b.job_id}`);
    if(job.email && env.AGENTMAIL_API_KEY) try{await sendEmail(job.email,`MedBill — Audit ready${b.savings_estimate?' ('+b.savings_estimate+')':''}`, `Hi,\n\nYour audit is complete.\n\nView: ${env.SITE_URL||'https://medbill.ai'}/report/${b.job_id}\n\nErrors: ${b.error_count||0}\nSavings: ${b.savings_estimate||'N/A'}`,env);}catch(e){}
    return json({success:true,report_url:`/report/${b.job_id}`});
  }catch(e){return json({error:'Failed'},500);}
});

// GET /api/queue/next — VPS cron pulls next job
router.get('/api/queue/next', async (req, env) => {
  try{
    const list=await env.MEDBILL_KV.list({prefix:'queue:'});
    if(!list.keys.length) return json({jobs:[]});
    const entries=[];
    for(const k of list.keys){const v=await env.MEDBILL_KV.get(k.name);if(v) entries.push({key:k.name,job:JSON.parse(v)});}
    entries.sort((a,b)=>a.job.createdAt-b.job.createdAt);
    for(const e of entries){
      if(e.job.status==='queued'){
        e.job.status='processing';e.job.step=1;
        await env.MEDBILL_KV.put(e.key,JSON.stringify(e.job));
        return json({job:e.job,job_id:e.job.id,download_url:e.job.fileName?`${env.SITE_URL||'https://medbill.ai'}/api/download/${e.job.id}/${e.job.fileName}`:null});
      }
    }
    return json({jobs:[]});
  }catch(e){return json({error:'Queue failed'},500);}
});

// GET /api/download/:id/:name
router.get('/api/download/:id/:name', async (req, env) => {
  try{
    const obj=await env.BILLS_BUCKET?.get(`bills/${req.params.id}/${req.params.name}`);
    if(obj) return new Response(obj.body,{headers:{'Content-Type':obj.httpMetadata?.contentType||'application/octet-stream','Content-Disposition':`attachment; filename="${req.params.name}"`}});
    return json({error:'Not found'},404);
  }catch(e){return json({error:'Failed'},500);}
});

// POST /api/stripe/webhook
router.post('/api/stripe/webhook', async (req, env) => {
  try{
    const sig=req.headers.get('stripe-signature');
    if(!sig) return json({error:'Missing signature'},400);
    const body=await req.text();
    const Stripe=require('stripe'),stripe=Stripe(env.STRIPE_SECRET_KEY);
    let event;
    try{event=stripe.webhooks.constructEvent(body,sig,env.STRIPE_WEBHOOK_SECRET);}catch(e){return json({error:'Invalid signature'},401);}
    if(event.type==='checkout.session.completed'){
      const s=event.data.object;
      if(s.metadata?.job_id){const j=await env.MEDBILL_KV.get(`job:${s.metadata.job_id}`);if(j){const job=JSON.parse(j);job.plan=s.metadata.plan;job.payment_status='paid';await env.MEDBILL_KV.put(`job:${s.metadata.job_id}`,JSON.stringify(job));}}
    }
    return json({received:true});
  }catch(e){return json({error:'Webhook failed'},500);}
});

router.all('*', ()=>json({error:'Not found'},404));

async function sendEmail(to,subject,text,env){
  if(!env.AGENTMAIL_API_KEY) return;
  await fetch('https://api.agentmail.to/v1/send',{method:'POST',headers:{'Authorization':`Bearer ${env.AGENTMAIL_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({to:[{email:to}],subject,text})});
}

export async function onRequest(context){return router.handle(context.request,context.env);}
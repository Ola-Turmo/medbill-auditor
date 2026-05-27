// POST /api/upload — Accept bill file, create job
export async function onRequest(context) {
  const { request, env } = context;
  let file, email;
  try {
    const fd = await request.formData();
    file = fd.get('file');
    email = fd.get('email') || '';
  } catch(e) { return json({error:'No file provided'},400); }
  if (!file) return json({error:'No file'},400);
  const ext = (file.name||'bill.pdf').split('.').pop()?.toLowerCase();
  if (!['pdf','jpg','jpeg','png'].includes(ext)) return json({error:'Invalid type. PDF, JPG, PNG only.'},400);
  if (file.size > 10*1024*1024) return json({error:'File too large. Max 10MB.'},413);
  const jobId = crypto.randomUUID();
  const job = {id:jobId,status:'queued',step:0,email,fileName:file.name,fileType:ext,fileSize:file.size,plan:'free',createdAt:Date.now(),updatedAt:Date.now()};
  if (env.BILLS_BUCKET && file.arrayBuffer) await env.BILLS_BUCKET.put(`bills/${jobId}/${file.name}`, await file.arrayBuffer(), {httpMetadata:{contentType:file.type}});
  if (env.MEDBILL_KV) {
    await env.MEDBILL_KV.put(`job:${jobId}`, JSON.stringify(job), {expirationTtl:86400*7});
    await env.MEDBILL_KV.put(`queue:${jobId}`, JSON.stringify(job), {expirationTtl:86400});
  }
  if (email && env.AGENTMAIL_API_KEY) try {
    await fetch('https://api.agentmail.to/v1/send',{method:'POST',headers:{'Authorization':`Bearer ${env.AGENTMAIL_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({to:[{email:to}],subject:'MedBill — Your bill is being analyzed',text:`Hi,\n\nWe received your bill and are analyzing it.\n\nCheck: ${env.SITE_URL||'https://medbill-auditor.pages.dev'}/status?id=${jobId}`})});
  } catch(e) {}
  return json({success:true,job_id:jobId,status_url:`/status?id=${jobId}`},201);
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

// POST /api/report — Receive audit results from VPS
export async function onRequest(context) {
  const { request, env } = context;
  try {
    const b = await request.json();
    if (!b.job_id) return json({error:'Missing job_id'},400);
    if (!env.MEDBILL_KV) return json({error:'KV not configured'},500);
    const js = await env.MEDBILL_KV.get(`job:${b.job_id}`);
    if (!js) return json({error:'Job not found'},404);
    const job = JSON.parse(js);
    Object.assign(job, {status:'completed',step:4,updatedAt:Date.now(),plan:b.plan||job.plan,findings:b.findings||[],dispute_letter:b.dispute_letter,phone_script:b.phone_script,rate_comparisons:b.rate_comparisons||[],billed_amount:b.billed_amount,service_count:b.service_count,error_count:b.error_count||(b.findings?b.findings.length:0),savings_estimate:b.savings_estimate,report_id:b.job_id});
    await env.MEDBILL_KV.put(`report:${b.job_id}`, JSON.stringify(job), {expirationTtl:86400*30});
    await env.MEDBILL_KV.put(`job:${b.job_id}`, JSON.stringify(job));
    await env.MEDBILL_KV.delete(`queue:${b.job_id}`);
    if (job.email && env.AGENTMAIL_API_KEY) try {
      await fetch('https://api.agentmail.to/v1/send',{method:'POST',headers:{'Authorization':`Bearer ${env.AGENTMAIL_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({to:[{email:job.email}],subject:`MedBill — Audit ready${b.savings_estimate?' ('+b.savings_estimate+')':''}`, text:`Hi,\n\nYour audit is complete.\n\nView: ${env.SITE_URL||'https://medbill-auditor.pages.dev'}/report/${b.job_id}\n\nErrors: ${b.error_count||0}\nSavings: ${b.savings_estimate||'N/A'}`})});
    } catch(e) {}
    return json({success:true,report_url:`/report/${b.job_id}`});
  } catch(e) { return json({error:'Failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

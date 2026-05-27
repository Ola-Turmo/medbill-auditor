// GET /api/report/:id
export async function onRequest(context) {
  const { env, params } = context;
  try {
    const id = params.id;
    let r = await env.MEDBILL_KV?.get(`report:${id}`);
    if (r) return json(JSON.parse(r));
    const j = await env.MEDBILL_KV?.get(`job:${id}`);
    if (!j) return json({error:'Not found'},404);
    const job = JSON.parse(j);
    if (job.status !== 'completed') return json({error:'Not ready',status:job.status},202);
    return json({id,plan:job.plan||'free',billed_amount:job.billed_amount,service_count:job.service_count,error_count:job.error_count||0,findings:job.findings||[],dispute_letter:job.dispute_letter,phone_script:job.phone_script,rate_comparisons:job.rate_comparisons||[]});
  } catch(e) { return json({error:'Failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

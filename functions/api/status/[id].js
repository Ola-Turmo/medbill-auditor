// GET /api/status/:id
export async function onRequest(context) {
  const { env, params } = context;
  try {
    const j = await env.MEDBILL_KV?.get(`job:${params.id}`);
    if (!j) return json({error:'Not found'},404);
    const job = JSON.parse(j);
    return json({id:job.id,status:job.status,step:job.step||0,email:job.email||'',error_count:job.error_count||0,savings_estimate:job.savings_estimate||null,report_id:job.report_id||null,plan:job.plan||'free'});
  } catch(e) { return json({error:'Failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

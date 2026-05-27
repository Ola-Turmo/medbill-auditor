// GET /api/download/:id/:name — Download uploaded bill file
export async function onRequest(context) {
  const { env, params } = context;
  try {
    const obj = await env.BILLS_BUCKET?.get(`bills/${params.id}/${params.name}`);
    if (obj) return new Response(obj.body, {headers:{'Content-Type':obj.httpMetadata?.contentType||'application/octet-stream','Content-Disposition':`attachment; filename="${params.name}"`}});
    return json({error:'Not found'},404);
  } catch(e) { return json({error:'Failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

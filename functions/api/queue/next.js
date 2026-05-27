// GET /api/queue/next — VPS cron pulls next job
export async function onRequest(context) {
  const { env } = context;
  try {
    if (!env.MEDBILL_KV) return json({error:'KV not configured'},500);
    const list = await env.MEDBILL_KV.list({prefix:'queue:'});
    if (!list.keys.length) return json({jobs:[]});
    const entries = [];
    for (const k of list.keys) {
      const v = await env.MEDBILL_KV.get(k.name);
      if (v) entries.push({key:k.name,job:JSON.parse(v)});
    }
    entries.sort((a,b) => a.job.createdAt - b.job.createdAt);
    for (const e of entries) {
      if (e.job.status === 'queued') {
        e.job.status = 'processing'; e.job.step = 1;
        await env.MEDBILL_KV.put(e.key, JSON.stringify(e.job));
        return json({job:e.job,job_id:e.job.id,download_url:e.job.fileName?`${env.SITE_URL||'https://medbill-auditor.pages.dev'}/api/download/${e.job.id}/${e.job.fileName}`:null});
      }
    }
    return json({jobs:[]});
  } catch(e) { return json({error:'Queue failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

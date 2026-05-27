// POST /api/stripe/webhook — Stripe payment handler
export async function onRequest(context) {
  const { request, env } = context;
  try {
    const sig = request.headers.get('stripe-signature');
    if (!sig) return json({error:'Missing signature'},400);
    const body = await request.text();
    if (!env.STRIPE_SECRET_KEY) return json({error:'Stripe not configured'},500);
    const Stripe = require('stripe');
    const stripe = Stripe(env.STRIPE_SECRET_KEY);
    let event;
    try { event = stripe.webhooks.constructEvent(body, sig, env.STRIPE_WEBHOOK_SECRET); }
    catch(e) { return json({error:'Invalid signature'},401); }
    if (event.type === 'checkout.session.completed') {
      const s = event.data.object;
      if (s.metadata?.job_id && env.MEDBILL_KV) {
        const j = await env.MEDBILL_KV.get(`job:${s.metadata.job_id}`);
        if (j) { const job=JSON.parse(j); job.plan=s.metadata.plan; job.payment_status='paid'; await env.MEDBILL_KV.put(`job:${s.metadata.job_id}`, JSON.stringify(job)); }
      }
    }
    return json({received:true});
  } catch(e) { return json({error:'Webhook failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

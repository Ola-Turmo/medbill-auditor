// POST /api/stripe/checkout — Create Stripe checkout session
export async function onRequest(context) {
  const { request, env } = context;
  try {
    if (request.method !== 'POST') return json({error:'POST required'},405);
    const b = await request.json();
    const { plan, job_id, success_url, cancel_url } = b;
    const priceMap = {'full-audit': env.STRIPE_FULL_AUDIT_PRICE_ID, 'b2b-starter': env.STRIPE_B2B_STARTER_PRICE_ID, 'b2b-pro': env.STRIPE_B2B_PRO_PRICE_ID};
    const priceId = priceMap[plan];
    if (!priceId) return json({error:'Invalid plan'},400);
    const mode = ['b2b-starter','b2b-pro'].includes(plan) ? 'subscription' : 'payment';
    const Stripe = require('stripe');
    const stripe = Stripe(env.STRIPE_SECRET_KEY);
    const session = await stripe.checkout.sessions.create({
      mode, line_items: [{price:priceId, quantity:1}],
      metadata: {plan, job_id: job_id || ''},
      success_url: success_url || `${env.SITE_URL||'https://medbill-auditor.pages.dev'}/report/${job_id||'success'}?checkout=success`,
      cancel_url: cancel_url || `${env.SITE_URL||'https://medbill-auditor.pages.dev'}/pricing`,
    });
    return json({url:session.url, session_id:session.id});
  } catch(e) { return json({error:'Checkout failed'},500); }
}
function json(d,s=200){return new Response(JSON.stringify(d),{status:s,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}});}

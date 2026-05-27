// Serve checkout.html for /checkout
export async function onRequest(context) {
  const url = new URL(context.request.url);
  url.pathname = '/checkout.html';
  return context.env.ASSETS.fetch(url);
}

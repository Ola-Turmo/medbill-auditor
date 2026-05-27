// Serve login.html for /login
export async function onRequest(context) {
  const url = new URL(context.request.url);
  url.pathname = '/login.html';
  return context.env.ASSETS.fetch(url);
}

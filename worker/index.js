export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.hostname = 'website-apexlab.pages.dev';
    const newRequest = new Request(url.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: 'follow',
    });
    return fetch(newRequest);
  },
};

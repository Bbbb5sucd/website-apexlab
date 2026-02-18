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

    const response = await fetch(newRequest);
    const newResponse = new Response(response.body, response);

    // === Security Headers ===
    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    newResponse.headers.set('X-Frame-Options', 'SAMEORIGIN');
    newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    newResponse.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

    // === Performance / Caching ===
    const pathname = url.pathname;

    if (pathname.match(/\.(css|js)$/)) {
      // Cache CSS/JS for 1 week
      newResponse.headers.set('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400');
    } else if (pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico|woff2?)$/)) {
      // Cache images/fonts for 1 month
      newResponse.headers.set('Cache-Control', 'public, max-age=2592000, stale-while-revalidate=86400');
    } else if (pathname.match(/\.(xml|txt)$/)) {
      // Cache sitemap/robots for 1 day
      newResponse.headers.set('Cache-Control', 'public, max-age=86400');
    } else {
      // HTML pages — short cache with revalidation
      newResponse.headers.set('Cache-Control', 'public, max-age=3600, stale-while-revalidate=86400');
    }

    // === Content Language hint ===
    newResponse.headers.set('Content-Language', 'ar, en');

    return newResponse;
  },
};

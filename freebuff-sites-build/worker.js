export default {
  async fetch(request, env) {
    // 1. Pass through to the static asset layer first.
    let response = await env.ASSETS.fetch(request);

    // 2. Deep-link fallback: pages served from a nested URL (e.g. /blog/post-14)
    //    resolve relative asset URLs like /blog/script.js. If such a request 404s,
    //    progressively strip leading path segments until an existing asset is found
    //    (e.g. /script.js). Extension-less misses (true page routes like /blog/post-14)
    //    are served the app shell — the SPA router inside index.html parses the real
    //    pathname and decides what to display.
    if (response.status === 404) {
      const url = new URL(request.url);
      const lastSegment = url.pathname.split('/').pop() || '';

      const shell = () => env.ASSETS.fetch(new Request(url.origin + '/index.html'));

      if (!lastSegment.includes('.')) {
        // Extension-less path (a "page" URL): serve the SPA shell and let the router handle it.
        response = await shell();
      } else {
        const segments = url.pathname.split('/').filter(Boolean);
        while (segments.length > 1) {
          segments.shift();
          const candidate = '/' + segments.join('/');
          const probe = await env.ASSETS.fetch(new Request(url.origin + candidate, { method: 'GET' }));
          if (probe.status === 404) {
            if (probe.body) await probe.body.cancel();
            continue;
          }
          return new Response(probe.body, probe);
        }
      }
    }

    return response;
  }
};

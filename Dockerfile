# syntax=docker/dockerfile:1

# Static marketing site served by Caddy. No build step, no runtime dependencies
# beyond the web server.
FROM caddy:2.11.7-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY site/ /srv/

EXPOSE 80 443

# Internal only: never published by compose. Caddy answers on 8081 even when
# SITE_ADDRESS enables automatic HTTPS on 80/443.
HEALTHCHECK --interval=30s --timeout=4s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8081/healthz | grep -q ok || exit 1

# Caddy runs as root in the official image, but the container is expected to be
# started with `--cap-drop ALL --cap-add NET_BIND_SERVICE` (see compose) so it
# can bind 80/443 and nothing else.

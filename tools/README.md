# Tooling

## `og-card.html`

Source for the 1200×630 social sharing image (`site/assets/img/og.png`). It is deliberately outside
`site/` so it is never published.

Serve the repository root and screenshot the page at exactly 1200×630:

```sh
python3 -m http.server 8097
# open http://127.0.0.1:8097/tools/og-card.html at a 1200×630 viewport
```

Save the capture as `site/assets/img/og.png`. The meta tags in `site/index.html` reference that path
with the absolute `https://tatutime.com/` origin.

Screenshots of the product itself (`site/assets/img/shot-*.png`) come from a real TatuTime
instance with a throwaway data directory and fictional demo data. Capture desktop views at 1440×803 and the mobile hero at a narrow portrait width; keep the browser chrome out of the crop.

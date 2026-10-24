# AI Agent Rules — Tucano Time Website

Repository-specific rules for the marketing site at `tucanotime.com`. The shared organisation
rules live in [`AgentRules/`](AgentRules/README.md), synced from
[TucanoAgentRules](https://github.com/TucanoTechnology/TucanoAgentRules); this file records what is
specific to this repository.

## What this repository is

A static marketing site for Tucano Time, the free, self-hosted timesheet and invoicing product.
It advertises the product and points people to the source repository; it is **not** the product and
must never collect or process user data.

- **Stack:** hand-written HTML, CSS and vanilla JavaScript. No build step, no framework, no npm.
- **Runtime:** either GitHub Pages or the `Caddyfile` container in this repository.
- **Deployable tree:** `site/`. Everything outside it is documentation, tooling or container
  configuration and is not published.

## Non-negotiable rules

1. **No third-party requests.** No analytics, telemetry, cookies, tracking pixels, external fonts,
   CDN scripts, embedded videos or remote images. The page must render and work fully offline. If a
   change would add an external origin, it needs an explicit maintainer decision and a matching CSP
   update in `Caddyfile`.
2. **Truthful claims only.** Verify every feature, security property and storage detail against
   `TucanoTechnology/TucanoTime` (source, `docs/`, `openapi.json`) before publishing it. Do not
   describe roadmap items as shipped, do not invent limits, and do not add a hosted/cloud tier:
   self-hosting is the product.
3. **Free means free.** Say AGPL-3.0, no seat count, no invoice limit, no credit card. Never imply a
   trial, paid plan or vendor cloud.
4. **AI in development is not AI in the product.** AI tools are used to build Tucano Time and this
   site; say so. The product and this site must never send user data to AI, add an AI feature, embed a
   chatbot/model or add a third-party form. Network access is limited to integrations the operator
   configures (SMTP, calendar, SSO, accounting sync) plus the anonymous ECB reference-rate feed.
   Keep the wording exact: "built with AI, but AI never touches your data" — never "no AI was
   involved".
5. **Accessibility does not regress.** Keyboard-operable navigation and tabs, visible focus,
   labelled controls, `aria-selected`/`aria-expanded` kept correct, contrast preserved in every
   section, and all motion disabled under `prefers-reduced-motion`. Check both 390 px and desktop.
6. **Brand assets are the source of truth.** Use the toucan and wordmark in `site/assets/brand/`
   without recolouring, cropping or stretching. The pixel art is scaled with
   `image-rendering: pixelated`; do not add filters to it (Firefox renders a white box behind
   transformed filtered pixel art).
7. **Screenshots come from the real product.** Use a throwaway data directory seeded with fictional
   demo data. Never commit a screenshot containing a real customer, invoice, email address or
   credential. Desktop captures are 1440×803; the mobile hero is a narrow portrait capture (currently 500×758, the smallest headless Firefox window).
8. **Security headers stay on.** The container relies on the CSP, `nosniff`, frame denial, referrer
   policy and HSTS in `Caddyfile`. Do not weaken them for convenience; if Pages is used, note that
   GitHub Pages cannot set these headers, which is one reason the container exists.

## Workflow

- This repository is **`main`-only**. Branch from `main`, open a pull request, merge back into
  `main`. Do not create a `develop` branch.
- Preview with `python3 -m http.server -d site 8080`. Run the checks with
  `python3 tools/check-site.py` (links, assets, ids, inline-script/style and external-resource
  rules) and `docker build -t tucanotime-website .` (Caddyfile + image). CI runs both on every
  pull request.
- Keep the container image multi-arch-safe: no amd64-only binaries, no architecture-specific assets.
- When changing content that mentions a version, feature or security property, update the product
  documentation link if needed and re-check the claim at the source.
- Do not commit generated caches, local `Data/`, `.env` files or TLS state.

## Deployment expectations

- `push` to `main` triggers the Pages workflow and the container workflow.
- The Pages artifact is `site/`; the custom domain lives in `site/CNAME` and in the repository's
  Pages settings.
- The container publishes `ghcr.io/tucanotechnology/tucanotime-website` for amd64 and arm64.
- DNS is an operator step, documented in `README.md`; do not assume it is configured in code.

## Contribution message

The site must visibly encourage people to contribute to
[`TucanoTechnology/TucanoTime`](https://github.com/TucanoTechnology/TucanoTime): the "Built in the
open" section, the GitHub navigation link, the footer links and the FAQ answer are part of the
product story. Do not remove them in a redesign.

<!-- shared-rules-table:begin -->
| Area | Rules |
| --- | --- |
| API & data contracts | [`AgentRules/coding/api-and-data-contracts.md`](AgentRules/coding/api-and-data-contracts.md) |
| Branching & git | [`AgentRules/coding/branching-and-git.md`](AgentRules/coding/branching-and-git.md) |
| Code review | [`AgentRules/coding/code-review.md`](AgentRules/coding/code-review.md) |
| Dependencies | [`AgentRules/coding/dependencies.md`](AgentRules/coding/dependencies.md) |
| Peak-hour warnings | [`AgentRules/generic/peak-hours.md`](AgentRules/generic/peak-hours.md) |
| Principles | [`AgentRules/generic/principles.md`](AgentRules/generic/principles.md) |
| Ticket template | [`AgentRules/project-management/ticket-template.md`](AgentRules/project-management/ticket-template.md) |
| Ticket workflow | [`AgentRules/project-management/workflow.md`](AgentRules/project-management/workflow.md) |
| Security | [`AgentRules/security/security.md`](AgentRules/security/security.md) |
| Contract tests | [`AgentRules/test/contract.md`](AgentRules/test/contract.md) |
| Performance tests | [`AgentRules/test/performance.md`](AgentRules/test/performance.md) |
| Browser & end-to-end tests | [`AgentRules/test/ui.md`](AgentRules/test/ui.md) |
| Unit tests | [`AgentRules/test/unit.md`](AgentRules/test/unit.md) |
<!-- shared-rules-table:end -->

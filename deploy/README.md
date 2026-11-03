# Railway deployment

The repository-root Dockerfile runs `python3 ai/server.py` as a non-root user
The Python standard-library server serves static files only from `web/dist` and handles the recommendation API on the same origin
It listens on `0.0.0.0:$PORT` with an 8080 default, supports video byte ranges, and serves `/healthz` for readiness
Static text responses support gzip with a bounded memory cache and `Vary: Accept-Encoding`
Static responses keep `no-cache` and add `no-transform` so intermediaries preserve the server's encoding choice
Video, ZIP, font and image files are not recompressed; byte-range requests use the original bytes

In Railway, connect `ryeong03/pariview` on `main` with the repository root as the root directory
The Dockerfile is detected automatically; no build or start command override is needed
Generate a public domain targeting port 8080 and set the healthcheck path to `/healthz`
If choosing another target port, set the Railway `PORT` variable to the same value

Healthcheck settings are maintained in the Railway dashboard
New Railway services no longer accept legacy `railway.json` Config as Code

Live demo: https://pariview-production.up.railway.app/

The current service was deployed from the public GitHub repository URL
Automatic deploys require granting the Railway GitHub App access to this repository
Until that is connected, push the completed commit and open service Settings → Source → Upstream Repo → Check for updates → Update
Confirm the latest commit in Deployments and verify `/healthz` and the public page after deployment

## Recommendation configuration

Set these service variables directly in Railway, then apply the deployment

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Server-side Anthropic key; also accepted as an existing Virtual Key when a gateway is configured |
| `ANTHROPIC_BASE_URL` | Optional Messages-compatible gateway base URL supplied by the provider; omit for direct Anthropic access |
| `ANTHROPIC_AUTH_TOKEN` | Optional gateway Virtual Key; takes priority over `ANTHROPIC_API_KEY` on a gateway |
| `PARIVIEW_AI_ENABLED` | Set to `1` to enable provider calls |
| `PARIVIEW_AI_MODEL` | Exact model allowed by the provider, for example `claude-sonnet-4-6`; no automatic model switching |
| `PARIVIEW_AI_DEBUG` | Keep `0` normally; `1` enables only bounded HTTP status/error-type diagnostics |

A configured gateway uses `/v1/messages` with Bearer authentication; direct Anthropic access uses `x-api-key`
An existing Virtual Key in `ANTHROPIC_API_KEY` can remain there without reading or copying it
Provider redirects are rejected, and public status reports only `anthropic` or `litellm`, never the endpoint or key

Without these settings, the recommendation uses the prepared research-based defaults
Provider failures also fall back to those defaults; only a validated provider response is labelled as an AI recommendation
`GET /api/recommendation/status` reports configuration status without returning keys
`POST /api/recommendation` is handled by the server; browser code never calls the provider directly
See [the recommendation setup guide](../ai/README.md) for model documentation and validation scope

Run the browser checks against a deployed URL with:

```sh
PARIVIEW_BASE_URL=https://YOUR-DOMAIN uv run --with playwright python web/validate.py
```

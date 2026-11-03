# Railway deployment

The repository-root Dockerfile serves only `web/dist` through Nginx
It listens on `0.0.0.0:$PORT` with an 8080 default, supports video byte ranges, and serves `/healthz` for readiness

In Railway, connect `ryeong03/pariview` on `main` with the repository root as the root directory
The Dockerfile is detected automatically; no build or start command override is needed
Generate a public domain targeting port 8080 and set the healthcheck path to `/healthz`
If choosing another target port, set the Railway `PORT` variable to the same value

Healthcheck settings are maintained in the Railway dashboard
New Railway services no longer accept legacy `railway.json` Config as Code

Run the browser checks against a deployed URL with:

```sh
PARIVIEW_BASE_URL=https://YOUR-DOMAIN uv run --with playwright python web/validate.py
```

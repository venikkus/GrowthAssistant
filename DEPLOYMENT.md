# Deployment

The simplest durable deployment path for this MVP is Render:

- It gives the app a stable `*.onrender.com` URL.
- It can auto-deploy from the GitHub `main` branch.
- It supports custom domains with managed HTTPS certificates.

## 1. Push To GitHub

```bash
cd /Users/venikkus/Documents/bioplant
gh auth login -h github.com -w
gh repo create bioplant --private --source=. --remote=origin --push
```

If the GitHub repo already exists:

```bash
git remote add origin git@github.com:venikkus/REPO_NAME.git
git push -u origin main
```

## 2. Deploy On Render

1. Open Render and create a new Blueprint or Web Service from the GitHub repo.
2. Render will detect `render.yaml`.
3. Use these settings if configuring manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true`
   - Python: `3.11.9`
4. After deploy, Render will provide a stable URL like:

```text
https://plant-bacteria-match.onrender.com
```

## 3. Attach A Custom Domain

In Render:

1. Open the service.
2. Go to Settings -> Custom Domains.
3. Add your domain or subdomain.
4. Add the DNS records Render shows at your registrar or DNS provider.
5. Click Verify in Render after DNS propagates.

Suggested names:

- `plantbacteriamatch.com`
- `plantbacteriamatch.org`
- `pgpbmatch.com`
- `bio-plant-match.com`

For a subdomain of an existing domain:

```text
pgpb.your-domain.com
```

## Notes

This deploys the Streamlit MVP UI. The Snakemake genome pipeline is intended to run locally or on a compute server, then its generated tables can be committed, uploaded, or mounted for the web UI later.


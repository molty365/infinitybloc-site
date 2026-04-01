# Infinity Bloc

[![Netlify Status](https://api.netlify.com/api/v1/badges/7b253d9b-d604-4db1-b8f5-1c1d2df247f3/deploy-status)](https://app.netlify.com/sites/infinitybloc-site/deploys)

**AI Enablement Consultancy**

🌐 **Live:** https://infinitybloc-site.netlify.app

## About

Infinity Bloc helps businesses integrate AI into their operations - from strategy to implementation.

## Development

```bash
# Just static HTML - open index.html or use any local server
python -m http.server 8000
```

## Deployment

- **Production:** Auto-deploys on push to `main`
- **PR Previews:** Every PR gets a unique preview URL (posted as a comment)

## CMS

Decap CMS is available at `/admin/`.

### Editable content
- `content/site.json` — homepage content
- `content/team.json` — ownership/team page content
- `bp.json` — BP export
- `chains.json` — chain exports

### Regenerating the static pages
If you edit the JSON content manually, re-render the static HTML with:

```bash
python3 scripts/render-site.py
```

### Netlify setup required
To make Decap CMS work in production, enable these in Netlify for the site:
- Identity
- Git Gateway

Once enabled, `/admin/` will let you edit content and commit changes back to GitHub.

Built with ❤️ by Tobias 🦞

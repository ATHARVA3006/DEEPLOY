# 🚀 Deployer

**Deployer** is a developer-focused file hosting and website preview platform. Upload HTML/CSS/JS projects, get instant shareable links, and preview your websites live — all in one place.

## ✨ Features

- 📤 **File Upload** — Upload any files (HTML, CSS, JS, images, etc.)
- 🌐 **Live Website Preview** — Preview HTML projects directly in the browser
- 🔗 **Shareable Links** — Instant public links for every project
- 🔒 **Public/Private Projects** — Control who sees your work
- 👥 **Community** — Discover and explore public projects
- 📊 **Analytics** — Track views and downloads
- 💎 **Subscription Plans** — Free, Pro, and Premium tiers
- 🛡️ **Admin Dashboard** — Full platform management

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
cd codeshare
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit `http://localhost:8000`

## 🌐 Deploy to Railway

1. Push to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Add environment variables from `.env.example`
4. Deploy!

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DATABASE_URL` | PostgreSQL connection URL |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF |

## 🛡️ Admin Access

Visit `/admin-panel/` and login with your superuser credentials.

## 📁 Project Structure

```
deployer/
├── codeshare/           # Django project
│   ├── codeshare/       # Settings, URLs, WSGI
│   ├── repository/      # Main app (models, views, forms)
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── api/                 # Vercel serverless entry
├── requirements.txt
├── Procfile             # Railway/Heroku deploy
└── vercel.json          # Vercel config
```

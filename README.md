# Platform R&D

A minimalistic open source portfolio and blogging platform built with [Pelican](https://getpelican.com/), a Python static site generator.

## Overview

This is the source for **platformrnd.com** — a showcase of open source projects and platform engineering work by Aziz Kurbanov.

**Live site**: https://platformrnd.com

## Projects Featured

- **[robotics-k8s-infra](https://github.com/sqe/robotics-k8s-infra)** — Production-grade Kubernetes platform for cloud/edge robotics with KubeEdge, ROS2, ArgoCD, and Cilium
- **[urlstatus](https://github.com/sqe/urlstatus)** — Distributed health-check and monitoring service for infrastructure
- **[fizmatmod](https://github.com/sqe/fizmatmod)** — Physics and mathematical modeling library for computational simulation
- **[esddns](https://github.com/sqe/esddns)** — Enterprise-scale DNS and distributed naming service

## Tech Stack

- **Static Site Generator**: [Pelican](https://getpelican.com/) (Python)
- **Styling**: Custom minimalistic CSS
- **Deployment**: GitHub Pages via GitHub Actions
- **Content Format**: Markdown

## Directory Structure

```
platformrnd.com/
├── content/                    # Markdown articles and pages
│   ├── robotics-k8s-infra.md
│   ├── urlstatus.md
│   ├── fizmatmod.md
│   ├── esddns.md
│   └── pages/
│       └── about.md
├── theme/                      # Custom Pelican theme
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── page.html
│       ├── article.html
│       └── index_page.html
├── .github/workflows/
│   └── publish.yml             # GitHub Actions automation
├── pelicanconf.py              # Pelican configuration
├── requirements.txt            # Python dependencies
├── CNAME                        # Custom domain file
└── README.md
```

## Setup & Development

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Build Locally

```bash
pelican content -o output -s pelicanconf.py
```

The generated site will be in the `output/` directory.

### Development Server

```bash
pelican -l content -o output -s pelicanconf.py
```

This watches for changes and rebuilds automatically (requires `livereload` plugin).

## Adding Content

### Create a New Article

Add a new Markdown file in `content/`:

```markdown
Title: Article Title
Date: 2025-11-23
Category: Open Source Projects
Tags: tag1, tag2, tag3
Slug: article-slug

Article content here...
```

### Create a New Page

Add a new Markdown file in `content/pages/`:

```markdown
Title: Page Title
Date: 2025-11-23
Slug: page-slug

Page content here...
```

## Deployment

This repository uses **GitHub Actions** to automatically build and deploy the site to GitHub Pages.

**Workflow**: `.github/workflows/publish.yml`

When you push to the `main` branch:
1. GitHub Actions checks out the code
2. Installs Python dependencies
3. Builds the Pelican site
4. Deploys to the `gh-pages` branch
5. GitHub Pages serves the site

### GitHub Pages Configuration

Ensure your repository settings have:
- **Source**: `Deploy from a branch`
- **Branch**: `gh-pages` (auto-created by the workflow)
- **Folder**: `/ (root)`

## Customization

### Theme

Edit `theme/static/style.css` for styling changes.

Edit `theme/templates/` files for HTML layout changes.

### Site Configuration

Edit `pelicanconf.py` to customize:
- Site name, author, URL
- Timezone
- Theme
- Plugins

### Domain

The `CNAME` file points to `platformrnd.com`. Update it if using a different domain.

## License

Content and design © 2025 Aziz Kurbanov. See individual project repositories for their respective licenses.

## Author

**Aziz Kurbanov**

- GitHub: https://github.com/sqe
- Website: https://platformrnd.com

# Deployment to GitHub Pages

## Prerequisites
1. GitHub account
2. Git installed locally
3. Repository created on GitHub

## Initial Setup

### 1. Create GitHub Repository
```powershell
# Navigate to your library folder
cd "C:\Modding\Bethesda Library"

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: MkDocs setup with Bethesda modding library structure"

# Add your GitHub repository as remote (replace with your username/repo)
git remote add origin https://github.com/yourusername/bethesda-library.git

# Push to GitHub
git push -u origin main
```

### 2. Deploy to GitHub Pages

Once your files are pushed to GitHub, deploy the site:

```powershell
# Build and deploy to gh-pages branch
& "c:/Modding/Bethesda Library/.venv/Scripts/python.exe" -m mkdocs gh-deploy
```

This command will:
- Build your documentation site
- Create/update a `gh-pages` branch
- Push the built site to GitHub
- Your site will be live at: `https://yourusername.github.io/bethesda-library/`

### 3. Enable GitHub Pages (if needed)

If this is your first deployment:
1. Go to your repository on GitHub
2. Click **Settings**
3. Click **Pages** (in left sidebar)
4. Under "Source", ensure it's set to "Deploy from a branch"
5. Select branch: `gh-pages` and folder: `/ (root)`
6. Click **Save**

Your site should be live in a few minutes!

## Updating the Site

After making changes to your markdown files:

```powershell
# Test locally first
& "c:/Modding/Bethesda Library/.venv/Scripts/python.exe" -m mkdocs serve

# Visit http://localhost:8000 to preview

# When satisfied, commit and push your changes
git add .
git commit -m "Update documentation"
git push

# Deploy the updated site
& "c:/Modding/Bethesda Library/.venv/Scripts/python.exe" -m mkdocs gh-deploy
```

## Automation (Optional)

You can also set up GitHub Actions to automatically deploy when you push to main:

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy MkDocs
on:
  push:
    branches:
      - main
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --force
```

With this workflow, every push to `main` automatically rebuilds and deploys your site!

## Troubleshooting

### Site not updating?
- Wait 2-3 minutes for GitHub Pages to rebuild
- Check Actions tab in your repo for build errors
- Clear your browser cache

### 404 errors?
- Verify gh-pages branch exists
- Check GitHub Pages settings
- Ensure mkdocs.yml navigation paths match actual files

### Missing files warnings?
- These are normal if you haven't created all the files in your navigation yet
- The site will still build and deploy
- Create placeholder files or remove from nav temporarily

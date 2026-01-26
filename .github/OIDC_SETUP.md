# OIDC Trusted Publishing Setup Checklist

Quick setup guide for PyPI OIDC trusted publishing with GitHub Actions.

## ✅ Setup Steps

### 1. Configure PyPI (One-Time)

Go to: https://pypi.org/manage/project/pydantic-ai-jupyter/settings/publishing/

Add a new trusted publisher with these **exact** values:

| Field | Value |
|-------|-------|
| **Owner** | `rgbkrk` |
| **Repository name** | `pydantic-ai-jupyter` |
| **Workflow name** | `publish.yml` |
| **Environment name** | `pypi` |

Click **Add**.

### 2. Create GitHub Environment (One-Time)

In GitHub repo settings:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `pypi`
4. Click **Configure environment**
5. (Optional) Add protection rules:
   - ☑️ Required reviewers: `rgbkrk`
   - ☑️ Deployment branches: Selected branches → `main` and tags

Click **Save protection rules**.

## 🚀 Publishing

After setup, publishing is simple:

```bash
# 1. Update version in pyproject.toml
# 2. Commit and push to main
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push origin main

# 3. Tag and push
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

The GitHub Action will automatically:
- ✅ Run tests
- ✅ Build package
- ✅ Publish to PyPI (via OIDC)
- ✅ Create GitHub Release
- ✅ Sign artifacts with Sigstore

## 🔍 Verification

- PyPI: https://pypi.org/project/pydantic-ai-jupyter/
- Releases: https://github.com/rgbkrk/pydantic-ai-jupyter/releases
- Actions: https://github.com/rgbkrk/pydantic-ai-jupyter/actions

## ⚠️ Important

- The environment name `pypi` must match exactly in both PyPI and GitHub
- The workflow file must be named `publish.yml`
- Don't store any PyPI tokens - OIDC handles authentication
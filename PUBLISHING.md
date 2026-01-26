# Publishing pydantic-ai-jupyter

This guide covers publishing releases to PyPI using GitHub Actions with OIDC trusted publishing.

## Overview

The project uses **trusted publishing** (OIDC) which means:
- No PyPI tokens stored in GitHub secrets
- GitHub Actions authenticates directly with PyPI
- More secure and easier to manage
- Automatic signing with Sigstore

## One-Time Setup

### 1. Configure PyPI Trusted Publishing

Visit https://pypi.org/manage/project/pydantic-ai-jupyter/settings/publishing/ and add a new publisher:

- **PyPI Project Name**: `pydantic-ai-jupyter`
- **Owner**: `rgbkrk`
- **Repository name**: `pydantic-ai-jupyter`
- **Workflow name**: `publish.yml`
- **Environment name**: `pypi`

Click "Add" to save.

### 2. Create GitHub Environment

In your GitHub repository:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name it: `pypi`
4. (Optional) Add protection rules:
   - Required reviewers: yourself
   - Wait timer: 0 minutes
   - Deployment branches: only `main` or tagged releases

This environment name must match what you configured in PyPI.

## Publishing a Release

### Standard Release Process

1. **Update version in `pyproject.toml`** (if not already done)
   ```toml
   version = "0.2.0"
   ```

2. **Commit and push to main**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

3. **Create and push a git tag**
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0 - Brief description"
   git push origin v0.2.0
   ```

4. **Watch the workflow**
   - Go to https://github.com/rgbkrk/pydantic-ai-jupyter/actions
   - The "Publish to PyPI" workflow will start automatically
   - It will:
     - Run tests on all Python versions
     - Build the package
     - Publish to PyPI via OIDC
     - Create a GitHub Release with signed artifacts

5. **Verify**
   - Check PyPI: https://pypi.org/project/pydantic-ai-jupyter/
   - Check GitHub Releases: https://github.com/rgbkrk/pydantic-ai-jupyter/releases

### Release Checklist

Before creating a tag:

- [ ] All tests pass on main branch
- [ ] Version updated in `pyproject.toml`
- [ ] `CHANGELOG.md` updated (if you have one)
- [ ] README reflects any new features
- [ ] Notebooks still work
- [ ] Documentation is current

## Manual Publishing (Fallback)

If you need to publish manually:

```bash
# Clean old builds
rm -rf dist/

# Build the package
uv build

# Verify contents
ls -lh dist/
tar -tzf dist/pydantic_ai_jupyter-*.tar.gz | head -20

# Publish with token
uv publish
# Or: uvx twine upload dist/*
```

You'll need a PyPI API token from https://pypi.org/manage/account/token/

## Workflow Details

The `.github/workflows/publish.yml` workflow:

1. **Triggers**: Automatically on git tags starting with `v*`
2. **Test job**: Runs full test suite on Python 3.10-3.13
3. **Build job**: Creates wheel and source distribution
4. **Publish job**: 
   - Uses OIDC to authenticate with PyPI
   - Publishes via `pypa/gh-action-pypi-publish`
   - Requires the `pypi` environment
5. **Release job**:
   - Signs artifacts with Sigstore
   - Creates GitHub Release
   - Attaches signed artifacts

## Troubleshooting

### "Environment protection rules not satisfied"

If the workflow waits for approval:
- Go to the Actions run
- Click "Review deployments"
- Approve the deployment to `pypi`

### "Trusted publishing exchange failure"

Check that:
- PyPI publisher settings match exactly:
  - Owner: `rgbkrk`
  - Repo: `pydantic-ai-jupyter`
  - Workflow: `publish.yml`
  - Environment: `pypi`
- The GitHub environment is named exactly `pypi`
- The workflow has `id-token: write` permission

### "Version already exists on PyPI"

You can't overwrite a published version. Increment the version number:
```bash
# Delete the local tag
git tag -d v0.2.0

# Update version in pyproject.toml
# Then create a new tag
git tag -a v0.2.1 -m "Release v0.2.1"
git push origin v0.2.1
```

### Manual deletion needed

If you pushed a tag by mistake:
```bash
# Delete local tag
git tag -d v0.2.0

# Delete remote tag
git push --delete origin v0.2.0
```

Then cancel the GitHub Actions workflow if it's running.

## Version Numbering

Follow semantic versioning:
- `0.x.y` - Pre-1.0 releases (current)
- `x.0.0` - Major (breaking changes)
- `x.y.0` - Minor (new features, backward compatible)
- `x.y.z` - Patch (bug fixes)

## Testing PyPI (TestPyPI)

To test before publishing to real PyPI:

1. Create a TestPyPI account at https://test.pypi.org
2. Set up trusted publishing there (same process)
3. Modify `publish.yml` temporarily to use TestPyPI:
   ```yaml
   - name: Publish distribution to TestPyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     with:
       repository-url: https://test.pypi.org/legacy/
   ```
4. Test install:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ \
       pydantic-ai-jupyter
   ```

## Resources

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [uv publish docs](https://docs.astral.sh/uv/guides/publish/)
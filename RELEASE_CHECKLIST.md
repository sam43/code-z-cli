# PyPI Release Checklist for codez-cli v0.2.0

## 1. Update Version
- [ ] Update `version` in `setup.py` to `0.2.0`
- [ ] Update `version` in `pyproject.toml` to `0.2.0`

## 2. Clean Previous Builds
- [ ] Remove old build artifacts: `rm -rf dist/ build/ *.egg-info/`

## 3. Build Distribution
- [ ] Install build tools: `pip install --upgrade build twine`
- [ ] Build package: `python -m build`

## 4. Check Distribution
- [ ] Run: `twine check dist/*`

## 5. Upload to PyPI
- [ ] Run: `twine upload dist/*`

## 6. Verify Release
- [ ] Check PyPI project page
- [ ] Test install: `pip install --upgrade codez-cli`

## 7. Tag Release in Git (optional)
- [ ] `git tag v0.2.0`
- [ ] `git push --tags`

## 8. (Optional) Test on TestPyPI
- [ ] Upload: `twine upload --repository testpypi dist/*`
- [ ] Install: `pip install --index-url https://test.pypi.org/simple/ codez-cli`

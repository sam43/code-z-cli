# PyPI Release Checklist for codez-cli vx.x.x

## 1. Update Version
- [ ] Update `version` in `pyproject.toml` to `x.x.x`

## 2. Ensure Version Utility
- [ ] Verify `version_utils.py` exists and contains `get_version()` function
- [ ] Confirm `setup.py` uses `get_version()` from `version_utils.py`

## 3. Clean Previous Builds
- [ ] Remove old build artifacts: `rm -rf dist/ build/ *.egg-info/`

## 4. Update Dependencies
- [ ] Review and update dependencies in `pyproject.toml` if necessary
- [ ] Update `requirements.txt` if used: `pip freeze > requirements.txt`

## 5. Run Tests
- [ ] Activate virtual environment: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
- [ ] Run test suite: `pytest` (or your preferred test command)
- [ ] Ensure all tests pass

## 6. Build Distribution
- [ ] Install/upgrade build tools: `pip install --upgrade build twine`
- [ ] Build package: `python -m build`

## 7. Check Distribution
- [ ] Run: `twine check dist/*`

## 8. (Optional) Test on TestPyPI
- [ ] Upload to TestPyPI: `twine upload --repository testpypi dist/*`
- [ ] Create a new virtual environment for testing
- [ ] Install from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ codez-cli`
- [ ] Test the installed package

## 9. Upload to PyPI
- [ ] Run: `twine upload dist/*`

## 10. Verify Release
- [ ] Check PyPI project page: https://pypi.org/project/codez-cli/
- [ ] Create a new virtual environment for testing
- [ ] Test install: `pip install --upgrade codez-cli`
- [ ] Run `codez --help` to ensure it works correctly

## 11. Tag Release in Git
- [ ] Create a new git tag: `git tag vx.x.x`
- [ ] Push the tag: `git push origin vx.x.x`

## 12. Update Documentation
- [ ] Update README.md with new version and any new features
- [ ] Update CHANGELOG.md (if you maintain one)

## 13. Create GitHub Release
- [ ] Go to GitHub repository
- [ ] Create a new release using the new tag
- [ ] Add release notes

## 14. Announce Release
- [ ] Inform users through appropriate channels (e.g., project website, mailing list, social media)

## 15. Post-Release
- [ ] Close milestone on GitHub (if used)
- [ ] Create new milestone for next version (if applicable)
- [ ] Review and update project roadmap
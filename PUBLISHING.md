# Publishing the Atrium SDK to PyPI

This is a step-by-step guide for the first PyPI release. If you've never published a Python package before, follow it top to bottom — there are no skipped steps.

> ⚠️ **Do not run these commands during normal development.** Publishing is a deliberate release action.

---

## 0. Confirm the package name is available

The PyPI registry is first-come-first-served. As of writing:

- `atrium-sdk` → **TAKEN** (by `brendon-garner-01/agent-network`, an unrelated prediction-market SDK)
- `atrium` → **TAKEN** (by MX Atrium, a financial data API)
- `monago-atrium` → **AVAILABLE** ✅ (this repo's chosen name)

Re-check before each release:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/monago-atrium/json
# 404 = available, 200 = taken
```

If the name has been claimed by someone else in the meantime, update `pyproject.toml`'s `[project].name` and rebuild.

---

## 1. Create accounts

You need two accounts (use the same email if you want):

1. **TestPyPI** — staging registry for trial releases: <https://test.pypi.org/account/register/>
2. **PyPI** — production registry: <https://pypi.org/account/register/>

Enable 2FA on both (TOTP via an authenticator app is fastest). PyPI requires 2FA for upload.

---

## 2. Generate API tokens

API tokens replace passwords for uploads. Generate one per registry:

- TestPyPI: <https://test.pypi.org/manage/account/token/>
- PyPI: <https://pypi.org/manage/account/token/>

For the very first upload of a new package name, scope the token to "entire account" — PyPI doesn't know the project name yet. After the first upload, regenerate a token scoped to the `monago-atrium` project only and discard the broad one.

Store the tokens in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJ...   # full token, including "pypi-" prefix

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpL...
```

Then `chmod 600 ~/.pypirc` so other users on the machine can't read it.

---

## 3. Build the distribution artifacts

From the repo root:

```bash
pip install --upgrade build twine
rm -rf dist/ build/ *.egg-info
python -m build
```

This produces:

```
dist/monago_atrium-0.1.0-py3-none-any.whl
dist/monago_atrium-0.1.0.tar.gz
```

Verify with twine that the metadata is well-formed before uploading:

```bash
twine check dist/*
# Expected: PASSED for both files
```

---

## 4. Dry-run on TestPyPI first

**Always do this on a new package.** TestPyPI is a separate registry — packages uploaded here do not appear on PyPI, but the upload mechanics are identical.

```bash
twine upload --repository testpypi dist/*
```

Then verify the install in a fresh virtualenv:

```bash
python -m venv /tmp/atrium-test
/tmp/atrium-test/bin/pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    monago-atrium
/tmp/atrium-test/bin/python -c "from monago_atrium import Atrium; print(Atrium.__module__)"
```

The `--extra-index-url` is needed because TestPyPI doesn't host runtime dependencies (`httpx`); the fallback resolves them from real PyPI.

If anything is wrong (broken metadata, missing files, wrong import name), fix it, **bump the version** in `pyproject.toml` (TestPyPI doesn't allow re-uploading the same version), and re-build. You cannot reuse `0.1.0` once uploaded — even to TestPyPI.

---

## 5. Publish to production PyPI

When TestPyPI looks good:

```bash
twine upload dist/*
```

Within a minute or two the package is live at <https://pypi.org/project/monago-atrium/>. Confirm:

```bash
python -m venv /tmp/atrium-prod
/tmp/atrium-prod/bin/pip install monago-atrium
/tmp/atrium-prod/bin/python -c "from monago_atrium import Atrium, GovernanceMetadata; print('ok')"
```

---

## 6. Tag the release in git

```bash
git tag -a v0.1.0 -m "Atrium SDK v0.1.0 — chat completions + governance metadata"
git push origin v0.1.0
```

If the repo lives on GitHub, also create a Release pointing at the tag with the relevant CHANGELOG section as the body.

---

## 7. Versioning rules

Follow [Semantic Versioning](https://semver.org/):

| Change kind | Version bump | Example |
|---|---|---|
| Bug fix, no API change | PATCH | 0.1.0 → 0.1.1 |
| New feature, backwards-compatible | MINOR | 0.1.1 → 0.2.0 |
| Breaking change (renamed function, removed field, changed argument) | MAJOR | 0.2.0 → 1.0.0 |

While the SDK is on `0.x`, the API is allowed to break between minor versions (this is the SemVer convention for pre-1.0). Once we tag `1.0.0`, breaking changes require a major bump.

Update `pyproject.toml`'s `version` AND `src/monago_atrium/__init__.py`'s `__version__` AND `src/monago_atrium/client.py`'s `_SDK_VERSION` in the same commit. Add a `CHANGELOG.md` entry.

---

## 8. After publishing

- Verify install works in a clean environment (see step 5).
- Watch the project page for download stats: <https://pypistats.org/packages/monago-atrium>.
- If a bad release slipped out, you can `twine upload --skip-existing` a `0.1.1` fix immediately — **do not delete** the broken version (PyPI generally allows deletion but it confuses downstream tooling). Use `pip install monago-atrium==0.1.1` to pin past it. You can mark the broken version yanked on PyPI's project page (Manage → Releases → Yank) — that hides it from resolvers without breaking pins.

---

## Common mistakes

- **Forgetting `__token__`** as the username. The literal string `__token__` (two underscores on each side) is the username when you authenticate with an API token.
- **Uploading without a unique version.** PyPI rejects re-uploads of the same `name + version`. Bump and re-build.
- **Tokens leaking into commits.** `.pypirc` is in `$HOME`, not the repo — keep it that way.
- **Skipping TestPyPI.** It costs five minutes and catches metadata bugs before they're permanent on real PyPI.

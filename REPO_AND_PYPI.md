# Git + PyPI from this folder

**Yes — this `edgameclaw/` tree can be the only thing you `git push` to GitHub *and* the same tree you use to build PyPI packages.**  
You do **not** need a separate folder for PyPI vs Git, as long as the repo root contains `pyproject.toml` and the `edgameclaw/` package (nested module).

The sibling **`old/edgameclaw/`** layout is only relevant if you still maintain a **legacy flat tree**; long-term, point your GitHub repo at **this** layout so one push updates both source and releases.

---

## README: PyPI vs GitHub

| File | Role |
|------|------|
| **`README_PYPI.md`** | Used in `pyproject.toml` → text on **pypi.org** (no huge GIFs). |
| **`README.md`** | **GitHub** landing page: video, GIFs, bilingual sections. |

`python -m build` embeds **`README_PYPI.md`** into package metadata. You do **not** strip `README.md` before publishing.

**GIFs in `edgameclaw/readme/`** are **not** included in the PyPI **wheel** (only PNG/JPEG/WebP/SVG/ICO under `readme/` are packaged). Large `.gif` demos stay on **GitHub**; `MANIFEST.in` also excludes them from **sdist**. This is separate from **`README_PYPI.md`** (the text shown on pypi.org).

---

## Build PyPI packages locally

From the directory that contains **`pyproject.toml`**:

```bash
cd /path/to/edgameclaw   # repo root with pyproject.toml

python -m pip install --upgrade build twine

# Bump version first in pyproject.toml and edgameclaw/__init__.py

python -m build          # creates dist/*.whl and dist/*.tar.gz
twine check dist/*
```

**Test upload (optional):** [TestPyPI](https://test.pypi.org)

```bash
twine upload --repository testpypi dist/*
pip install -i https://test.pypi.org/simple/ edgameclaw
```

**Production upload:**

```bash
twine upload dist/*
```

Use API token: username **`__token__`**, password **the token** from [PyPI → Account → API tokens](https://pypi.org/manage/account/token/).

Do **not** commit `dist/` or `build/` (they are in `.gitignore`).

---

## Publish from GitHub Actions (optional)

This repo includes:

- **`.github/workflows/ci.yml`** — on every push/PR to `main`/`master`, runs `python -m build` so a broken package fails CI.
- **`.github/workflows/publish-pypi.yml`** — on **`git push` of a tag** `v*` (e.g. `v0.1.2`), builds and runs `twine upload` (needs **`PYPI_API_TOKEN`** secret in the repo).

**Release checklist**

1. Bump **`version`** in `pyproject.toml` and `edgameclaw/__init__.py`.
2. Commit and push to GitHub.
3. Tag and push:

```bash
git tag v0.1.2
git push origin v0.1.2
```

4. If using the publish workflow, ensure **`PYPI_API_TOKEN`** is set under **Settings → Secrets and variables → Actions**.

You can also run **Publish to PyPI** manually from the Actions tab (**workflow_dispatch**).

---

## Legacy `old/edgameclaw/` (flat layout)

| | This `edgameclaw/` | `old/edgameclaw/` |
|---|-------------------|-------------------|
| Imports | `edgameclaw.server`, nested package | Flat `server.py`, `from generator import …` |
| Use | **Recommended** single source for Git + PyPI | Older clone-only layout |

Migrating: replace the GitHub repo contents with this tree (or merge carefully), then delete the duplicate workflow once CI passes.

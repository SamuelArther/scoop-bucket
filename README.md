# SamuelArther/scoop-bucket

[Scoop](https://scoop.sh) bucket for my own tools.

```
scoop bucket add samuelarther https://github.com/SamuelArther/scoop-bucket
scoop install samuelarther/fetchart
```

| App | What it is |
|---|---|
| [fetchart](https://github.com/SamuelArther/fetchart) | Download game art, achievements, posters, album covers and more from the command line |

Manifests are bumped automatically: `.github/workflows/bump.yml` checks for a new release every few hours, `scripts/bump.py` rewrites the manifest, and `.github/workflows/ci.yml` installs it with Scoop on Windows.

# Vendored third-party libraries

Bundled locally so that `outputs/visualizations/` runs with **no internet
connection and no CDN dependency** at runtime.

`scripts/build_html_visualization.py` copies these into
`outputs/visualizations/assets/vendor/` on every build. They live here rather
than under `outputs/` so that `--clean` can safely wipe the generated
directory without losing them.

| Library | Version | License | Purpose |
|---|---|---|---|
| [Cytoscape.js](https://js.cytoscape.org/) | 3.30.2 | MIT | Interactive graph rendering in every graph view |

Only the Cytoscape core is vendored — no layout extensions. The views use the
built-in `breadthfirst`, `cose`, `concentric`, `circle`, `grid` and `preset`
layouts, which keeps the runtime footprint to a single 365 kB file.

Exact download URLs, byte counts and SHA-256 digests are recorded in
`cytoscape/vendor.json`, and `tests/test_visualization.py` re-checks the digest
so a substituted file is detected.

## Re-vendoring

```bash
python3 - <<'PY'
import urllib.request, hashlib, pathlib, json
V = "3.30.2"
out = pathlib.Path("vendor/cytoscape"); out.mkdir(parents=True, exist_ok=True)
manifest = {"library": "Cytoscape.js", "version": V, "license": "MIT",
            "homepage": "https://js.cytoscape.org/", "files": {}}
for name in ("cytoscape.min.js", "LICENSE"):
    url = f"https://unpkg.com/cytoscape@{V}/dist/{name}" if name.endswith(".js") \
          else f"https://unpkg.com/cytoscape@{V}/{name}"
    data = urllib.request.urlopen(url, timeout=60).read()
    (out / name).write_bytes(data)
    manifest["files"][name] = {"url": url, "bytes": len(data),
                               "sha256": hashlib.sha256(data).hexdigest()}
(out / "vendor.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
```

Network access is needed only for this step, never to view the application.

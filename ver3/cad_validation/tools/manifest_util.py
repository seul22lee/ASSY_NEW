"""Artifact-hash manifest: build last, verify immediately, detect later drift.

Written after a real failure. A BM-002 simulation run wrote its manifest, and
four artifacts then reached their final contents afterwards — because a second,
partial run rewrote reports and one video while a manifest from the first run was
already on disk. The manifest looked complete and four of its hashes were wrong.

Two things allowed that, and this module closes both:

1. **The manifest was written but never verified.** A generator that hashes files
   and stops has no way to notice that a writer was still open, or that another
   process is mid-write. `build_manifest` re-reads and re-hashes every entry
   before returning, so a manifest that is wrong at birth cannot be written.

2. **Nothing could detect post-manifest mutation.** Once written, the manifest
   was just a file; anything could change an artifact underneath it. `verify`
   makes that detectable at any later point, and is what a regression test calls.

Deliberately dependency-light — hashlib, os and PyYAML only. This runs beside a
CAD toolchain, and a manifest utility that cannot run without the CAD stack is a
utility that gets skipped in exactly the situations where it matters.

The manifest NEVER hashes itself. A self-hash is unsatisfiable: writing the hash
into the file changes the file. It is excluded by name, and `verify` treats a
self-entry as an error rather than ignoring it.
"""

import hashlib
import os

MANIFEST_FILENAME = "artifact_hashes.yaml"

CHUNK = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def collect_entries(roots, here, exclude_names=(MANIFEST_FILENAME,), skip_dirs=("__pycache__",)):
    """Every file under `roots`, as manifest rows, in deterministic order.

    Ordering is by repo-relative path, sorted at the end rather than relying on
    the order os.walk happens to yield. Filesystem traversal order is not
    guaranteed, and a manifest whose row order varies between runs cannot be
    diffed — which is most of what a manifest is for.
    """
    rows = []
    for root in roots:
        if os.path.isfile(root):
            rows.append(_row(root, here))
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
            for fn in sorted(filenames):
                if fn in exclude_names:
                    continue
                rows.append(_row(os.path.join(dirpath, fn), here))
    rows.sort(key=lambda r: r["path"])
    return rows


def _row(path, here):
    return {
        "path": os.path.relpath(path, here).replace(os.sep, "/"),
        "bytes": os.path.getsize(path),
        "sha256": sha256_file(path),
    }


def verify(doc, here):
    """Differences between a manifest and what is on disk now. Empty means clean."""
    problems = []
    for row in doc.get("files", []):
        path = os.path.join(here, row["path"])
        if os.path.basename(row["path"]) == MANIFEST_FILENAME:
            problems.append({"path": row["path"], "problem": "SELF_ENTRY",
                             "detail": "a manifest cannot hash itself; writing the "
                                       "hash in would change the file"})
            continue
        if not os.path.exists(path):
            problems.append({"path": row["path"], "problem": "MISSING"})
            continue
        actual_bytes = os.path.getsize(path)
        actual_sha = sha256_file(path)
        if actual_sha != row["sha256"] or actual_bytes != row["bytes"]:
            problems.append({
                "path": row["path"], "problem": "CHANGED",
                "recorded_sha256": row["sha256"], "actual_sha256": actual_sha,
                "recorded_bytes": row["bytes"], "actual_bytes": actual_bytes,
            })
    return problems


class ManifestVerificationError(RuntimeError):
    """Raised when a manifest does not describe the files on disk."""


def build_manifest(roots, here, extra=None, exclude_names=(MANIFEST_FILENAME,)):
    """Build a manifest and verify it before returning it.

    CALL THIS LAST. Everything it records must already be written and closed:
    all numerical outputs, all plots and videos, all per-artifact metadata. The
    verification pass below catches a writer that is still open, but only
    because the hash it computes differs from the one it just recorded — it
    cannot make a half-written file whole.
    """
    doc = dict(extra or {})
    rows = collect_entries(roots, here, exclude_names=exclude_names)
    doc["file_count"] = len(rows)
    doc["files"] = rows

    problems = verify(doc, here)
    if problems:
        raise ManifestVerificationError(
            "manifest did not verify immediately after construction: %s" % problems)
    return doc


def write_manifest(doc, path):
    """Write the manifest. Nothing tracked may be written after this call."""
    import yaml
    with open(path, "w") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False, default_flow_style=False, width=120)
    return path

"""Shared video evidence library for the Ver3 CAD pilot.

A video here is an EVIDENCE ARTIFACT, not an animation. The rules it enforces:

* Every frame is drawn from the reference's own B-rep solids, posed by the same
  functions the validator uses. Nothing is a stand-in, a proxy box or a
  hand-drawn approximation.
* Surfaces are shaded per FACE. Each face is tessellated, filled with no edge
  stroke at all, and then only its own boundary is drawn. That is what keeps
  mesh diagonals off the screen: the triangles carry the shading and never the
  line work.
* The camera is fixed for the whole clip and is written into the manifest, so a
  reader can tell that nothing was reframed to make a frame look better.
* Every clip writes a manifest recording engine, source geometry signature,
  frame count, duration, codec, camera, state timeline, a trajectory hash over
  the exact pose samples used, and the output file's own SHA-256.

What a video can establish is that declared geometry moves through declared
states without passing through itself. It cannot establish a force, a strain or
a life, and the manifest says so in every case.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import cadval as cv

ENGINE = "cadquery-ocp tessellation + matplotlib painter + ffmpeg (libx264)"
DEFAULT_TOL = 0.35          # tessellation deflection, mm


# ------------------------------------------------------------------- geometry
def face_patches(shape, tol: float = DEFAULT_TOL) -> List[Dict]:
    """One entry per B-rep face: its triangles, and its boundary loops.

    The boundary is derived from the triangulation itself - an undirected edge
    that belongs to exactly one triangle is on the face's rim. That gives a
    clean outline for planar and curved faces alike without any internal
    diagonal ever being drawn.
    """
    out = []
    for f in shape.Faces():
        try:
            verts, tris = f.tessellate(tol)
        except Exception:
            continue
        if not tris:
            continue
        pts = np.array([[v.x, v.y, v.z] for v in verts], dtype=float)
        tri = np.array(tris, dtype=int)
        seen: Dict[Tuple[int, int], int] = {}
        for a, b, c in tri:
            for e in ((a, b), (b, c), (c, a)):
                k = (min(e), max(e))
                seen[k] = seen.get(k, 0) + 1
        rim = [k for k, n in seen.items() if n == 1]
        out.append({"points": pts, "triangles": tri, "rim": rim})
    return out


def body_patches(bodies, tol: float = DEFAULT_TOL) -> List[Dict]:
    rows = []
    for b in bodies:
        for p in face_patches(b.shape, tol):
            p["body_id"] = b.id
            rows.append(p)
    return rows


# --------------------------------------------------------------------- camera
class Camera:
    """Fixed orthographic review camera.

    Orthographic on purpose: a reviewer measuring a gap off a frame should not
    have to correct for perspective. `scale` is the half-height of the view in
    model units, so the framing is a stated number rather than an autoscale.
    """

    def __init__(self, eye, target, up=(0.0, 0.0, 1.0), scale=60.0):
        self.eye = np.array(eye, dtype=float)
        self.target = np.array(target, dtype=float)
        self.up = np.array(up, dtype=float)
        self.scale = float(scale)
        f = self.target - self.eye
        f /= np.linalg.norm(f)
        r = np.cross(f, self.up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.forward, self.right, self.upv = f, r, u

    def project(self, pts: np.ndarray) -> np.ndarray:
        d = pts - self.target
        return np.stack([d @ self.right, d @ self.upv, d @ self.forward], axis=-1)

    def at(self, pt) -> tuple:
        """Where a model point lands in the frame's data coordinates.

        Arrows and labels are anchored through this rather than by eye, so a
        camera change moves them with the geometry instead of stranding them.
        """
        q = self.project(np.array([pt], dtype=float))[0]
        return float(q[0]), float(q[1])

    def as_dict(self) -> Dict:
        return {"projection": "orthographic",
                "eye_mm": [round(float(v), 3) for v in self.eye],
                "target_mm": [round(float(v), 3) for v in self.target],
                "up": [round(float(v), 3) for v in self.up],
                "half_height_mm": self.scale,
                "fixed_for_whole_clip": True}


# -------------------------------------------------------------------- shading
def _shade(base_rgb, normals, light=(0.35, -0.75, 0.55), ambient=0.42):
    l = np.array(light, dtype=float)
    l /= np.linalg.norm(l)
    lam = np.abs(normals @ l)
    k = ambient + (1.0 - ambient) * lam
    return np.clip(np.array(base_rgb)[None, :] * k[:, None], 0.0, 1.0)


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rasterise(patches, camera: Camera, colors: Dict[str, str],
              width: int = 1280, height: int = 720, bg="#f4f5f7",
              *, edge_rgb=(0.09, 0.10, 0.12), edge_px: float = 1.0):
    """Z-buffered shaded raster of the B-rep faces, plus hidden-line-removed rims.

    A painter's-algorithm sort was tried first and is not good enough here: a
    large far wall has a nearer centroid than a small near feature, so back faces
    bled through and the result read as a wireframe. A real depth buffer is the
    only honest way to say "this face is in front of that one".

    Returns (rgb_uint8, world_extent) where the extent lets overlays be placed in
    model units on top of the image.
    """
    aspect = width / float(height)
    half_w, half_h = camera.scale * aspect, camera.scale
    zbuf = np.full((height, width), np.inf, dtype=np.float64)
    img = np.zeros((height, width, 3), dtype=np.float64)
    img[:, :] = _hex_to_rgb(bg)

    def to_px(pr):
        px = (pr[:, 0] + half_w) / (2 * half_w) * (width - 1)
        py = (half_h - pr[:, 1]) / (2 * half_h) * (height - 1)
        return px, py

    for p in patches:
        pr = camera.project(p["points"])
        px, py = to_px(pr)
        pz = pr[:, 2]
        tri = p["triangles"]
        n3 = np.cross(p["points"][tri[:, 1]] - p["points"][tri[:, 0]],
                      p["points"][tri[:, 2]] - p["points"][tri[:, 0]])
        ln = np.linalg.norm(n3, axis=1)
        ln[ln == 0] = 1.0
        n3 = n3 / ln[:, None]
        cols = _shade(_hex_to_rgb(colors.get(p["body_id"], "#9aa5b1")), n3)
        for i in range(tri.shape[0]):
            ia, ib, ic = tri[i]
            x0, x1_ = px[[ia, ib, ic]], py[[ia, ib, ic]]
            xmin = max(int(np.floor(x0.min())), 0)
            xmax = min(int(np.ceil(x0.max())), width - 1)
            ymin = max(int(np.floor(x1_.min())), 0)
            ymax = min(int(np.ceil(x1_.max())), height - 1)
            if xmax < xmin or ymax < ymin:
                continue
            xs = np.arange(xmin, xmax + 1)
            ys = np.arange(ymin, ymax + 1)
            gx, gy = np.meshgrid(xs, ys)
            ax_, ay_ = x0[0], x1_[0]
            bx, by = x0[1], x1_[1]
            cx, cy = x0[2], x1_[2]
            den = (by - cy) * (ax_ - cx) + (cx - bx) * (ay_ - cy)
            if abs(den) < 1e-12:
                continue
            l1 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
            l2 = ((cy - ay_) * (gx - cx) + (ax_ - cx) * (gy - cy)) / den
            l3 = 1.0 - l1 - l2
            m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            if not m.any():
                continue
            z = l1 * pz[ia] + l2 * pz[ib] + l3 * pz[ic]
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            win = m & (z < sub)
            if not win.any():
                continue
            sub[win] = z[win]
            img[ymin:ymax + 1, xmin:xmax + 1][win] = cols[i]

    # rims, depth-tested against the finished buffer so hidden edges stay hidden
    for p in patches:
        pr = camera.project(p["points"])
        px, py = to_px(pr)
        pz = pr[:, 2]
        for i0, i1 in p["rim"]:
            n = int(max(abs(px[i1] - px[i0]), abs(py[i1] - py[i0]))) + 2
            tt = np.linspace(0.0, 1.0, n)
            ex = px[i0] + (px[i1] - px[i0]) * tt
            ey = py[i0] + (py[i1] - py[i0]) * tt
            ez = pz[i0] + (pz[i1] - pz[i0]) * tt
            xi = np.rint(ex).astype(int)
            yi = np.rint(ey).astype(int)
            ok = (xi >= 0) & (xi < width) & (yi >= 0) & (yi < height)
            if not ok.any():
                continue
            xi, yi, ez = xi[ok], yi[ok], ez[ok]
            vis = ez <= zbuf[yi, xi] + 0.35
            if not vis.any():
                continue
            xs, ys = xi[vis], yi[vis]
            r = int(max(0, round(edge_px - 1)))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    xx = np.clip(xs + dx, 0, width - 1)
                    yy = np.clip(ys + dy, 0, height - 1)
                    img[yy, xx] = edge_rgb

    return (np.clip(img, 0, 1) * 255).astype(np.uint8), (-half_w, half_w, -half_h, half_h)


def new_canvas(img, extent, width=1280, height=720):
    """Put the finished raster into a 1:1 axes whose data units are model units,
    so overlays and arrows can be positioned in millimetres."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.imshow(img, extent=extent, origin="upper", interpolation="none", zorder=1)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def frame_rgb(fig) -> np.ndarray:
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return buf[:, :, :3].copy()


# --------------------------------------------------------------------- output
def write_mp4(frames: Sequence[np.ndarray], path: str, fps: int = 30,
              quality: int = 8) -> str:
    import imageio
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = imageio.get_writer(path, fps=fps, codec="libx264", quality=quality,
                           macro_block_size=8,
                           ffmpeg_params=["-pix_fmt", "yuv420p", "-profile:v", "high"])
    for f in frames:
        w.append_data(f)
    w.close()
    return path


def write_gif(frames: Sequence[np.ndarray], path: str, fps: int = 15,
              every: int = 2, scale: float = 0.5) -> str:
    import imageio
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    small = []
    for i, f in enumerate(frames):
        if i % every:
            continue
        im = Image.fromarray(f)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        small.append(np.asarray(im))
    imageio.mimsave(path, small, fps=fps, loop=0)
    return path


def probe_mp4(path: str) -> Dict:
    """Read back what was actually written, rather than what was intended."""
    import imageio
    import imageio_ffmpeg
    rd = imageio.get_reader(path)
    meta = rd.get_meta_data()
    n = 0
    for _ in rd:
        n += 1
    rd.close()
    return {"container_fps": meta.get("fps"),
            "container_duration_s": meta.get("duration"),
            "container_size_px": list(meta.get("size", ())),
            "frames_read_back": n,
            "codec_reported": meta.get("codec"),
            "ffmpeg_version": imageio_ffmpeg.get_ffmpeg_version()}


def trajectory_hash(samples: Sequence[Sequence[float]]) -> str:
    """A hash over the exact numbers the frames were drawn from.

    Rounded to 1e-6 before hashing so it is reproducible across runs but still
    changes if any pose in the clip changes.
    """
    body = "\n".join(",".join("%.6f" % float(v) for v in row) for row in samples)
    return hashlib.sha256(body.encode()).hexdigest()


def manifest(*, video_id: str, reference_id: str, path: str, here: str,
             geometry_signature: str, fps: int, width: int, height: int,
             frame_count: int, camera: Camera, timeline: List[Dict],
             traj_hash: str, assumptions: Dict, establishes: List[str],
             does_not_establish: List[str], extra: Optional[Dict] = None) -> Dict:
    rec = {
        "video_id": video_id,
        "reference_id": reference_id,
        "file": os.path.relpath(path, here),
        "kind": "REVIEW_EVIDENCE",
        "engine": ENGINE,
        "engine_versions": _versions(),
        "source_geometry_signature_sha256": geometry_signature,
        "geometry_source": ("the reference's own B-rep solids, posed by the same "
                            "functions the validator uses. No proxy geometry."),
        "fps": fps,
        "resolution_px": [width, height],
        "frame_count": frame_count,
        "duration_s": round(frame_count / float(fps), 4),
        "codec": "H.264 (libx264), yuv420p, MP4 container",
        "camera": camera.as_dict(),
        "state_timeline": timeline,
        "trajectory_sha256": traj_hash,
        "output_sha256": cv.sha256_file(path),
        "output_bytes": os.path.getsize(path),
        "container_readback": probe_mp4(path),
        "assumptions": assumptions,
        "claims_established": establishes,
        "claims_not_established": does_not_establish,
        "human_review": "HUMAN_REVIEW_PENDING",
    }
    if extra:
        rec.update(extra)
    return rec


def _versions() -> Dict:
    import matplotlib
    import imageio_ffmpeg
    import cadquery
    return {"cadquery": cadquery.__version__,
            "matplotlib": matplotlib.__version__,
            "imageio_ffmpeg": imageio_ffmpeg.__version__,
            "ffmpeg": imageio_ffmpeg.get_ffmpeg_version(),
            "numpy": np.__version__}


# ------------------------------------------------------------------- overlays
BOX = dict(boxstyle="round,pad=0.35", fc="white", ec="#3a3f45", lw=0.9, alpha=0.94)


def title_block(ax, lines: List[str], *, x=0.014, y=0.938, size=11.5,
                color="#1b1f24", weight="normal", ha="left", va="top", box=True):
    ax.text(x, y, "\n".join(lines), transform=ax.transAxes, fontsize=size,
            color=color, ha=ha, va=va, family="DejaVu Sans", weight=weight,
            bbox=BOX if box else None, zorder=20)


def state_banner(ax, text: str, *, color="#b03a2e", x=0.5, y=0.995):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=16, color="white",
            ha="center", va="top", weight="bold", zorder=21,
            bbox=dict(boxstyle="round,pad=0.42", fc=color, ec="none"))


def caveat(ax, text: str, *, y=0.018, color="#5a6068"):
    ax.text(0.5, y, text, transform=ax.transAxes, fontsize=10, color=color,
            ha="center", va="bottom", style="italic", zorder=20,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9ced4", lw=0.8,
                      alpha=0.92))


def arrow(ax, xy, dxy, text=None, *, color="#b03a2e", lw=3.4, size=13,
          toff=(0.0, 0.0), tha="center"):
    """A heavy motion or press arrow, in DATA coordinates."""
    x, y = xy
    dx, dy = dxy
    ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y), zorder=22,
                arrowprops=dict(arrowstyle="-|>,head_width=0.42,head_length=0.9",
                                lw=lw, color=color, shrinkA=0, shrinkB=0))
    if text:
        ax.text(x + dx * 0.5 + toff[0], y + dy * 0.5 + toff[1], text, color=color,
                fontsize=size, weight="bold", ha=tha, va="center", zorder=23,
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=color, lw=1.2))

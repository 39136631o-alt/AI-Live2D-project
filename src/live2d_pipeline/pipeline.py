"""Deterministic mask-based layer extraction. All coordinates are canvas pixels."""
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

MAX_PIXELS = 16_000_000


def load_image(path):
    with Image.open(path) as image:
        if image.width * image.height > MAX_PIXELS:
            raise ValueError(f"image exceeds {MAX_PIXELS} pixels")
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("animated images are unsupported")
        image.load()
        return ImageOps.exif_transpose(image).convert("RGBA")


def inspect_image(path):
    image = load_image(path)
    alpha = image.getchannel("A")
    return {
        "width": image.width, "height": image.height, "mode": "RGBA",
        "alpha_range": list(alpha.getextrema()), "visible_bbox": alpha.getbbox(),
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "warnings": (["No transparent background; no automatic background removal performed."]
                     if alpha.getextrema() == (255, 255) else []),
    }


def process(source, specification, output):
    """Extract bottom-to-top masks. Reject invalid input before creating output."""
    spec_path = Path(specification)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if spec.get("rights_confirmed") is not True:
        raise ValueError("rights_confirmed must be true for source and masks")
    if spec.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    entries = spec.get("layers")
    if not isinstance(entries, list) or not entries:
        raise ValueError("layers must be a nonempty list")
    source_image = load_image(source)
    prepared, seen = [], set()
    for entry in entries:
        name = entry.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
            raise ValueError("layer names must be safe ASCII identifiers, up to 64 characters")
        if name.casefold() in seen:
            raise ValueError("duplicate layer name")
        seen.add(name.casefold())
        # Paths in the manifest refer to trusted local inputs, relative to the manifest.
        mask_path = spec_path.parent / entry["mask"]
        with Image.open(mask_path) as raw:
            if raw.size != source_image.size:
                raise ValueError(f"mask size mismatch: {name}")
            if raw.mode != "L" or getattr(raw, "n_frames", 1) != 1:
                raise ValueError("masks must be single-frame 8-bit grayscale (L)")
            mask = raw.copy()
        alpha = ImageChops.multiply(source_image.getchannel("A"), mask)
        if alpha.getbbox() is None:
            raise ValueError(f"empty visible layer: {name}")
        layer = source_image.copy()
        layer.putalpha(alpha)
        prepared.append((name, layer, hashlib.sha256(mask_path.read_bytes()).hexdigest()))
    out = Path(output)
    # Never overwrite existing user files or partially merge old and new runs.
    out.mkdir(parents=True, exist_ok=False)
    (out / "layers").mkdir()
    preview = Image.new("RGBA", source_image.size)
    coverage = Image.new("L", source_image.size)
    layers = []
    for index, (name, layer, digest) in enumerate(prepared):
        filename = f"layers/{index:03d}_{name}.png"
        layer.save(out / filename)
        preview = Image.alpha_composite(preview, layer)
        coverage = ImageChops.lighter(coverage, layer.getchannel("A"))
        layers.append({"name": name, "file": filename, "order": index,
                       "bbox": layer.getchannel("A").getbbox(), "mask_sha256": digest})
    preview.save(out / "preview.png")
    # Diagnostic only: this is visible source not covered by any extracted layer.
    uncovered = ImageChops.subtract(source_image.getchannel("A"), coverage)
    uncovered.save(out / "uncovered.png")
    report = {"schema_version": 1, "artifact_type": "image_layer_intermediate",
              "cubism_model": False, "rights_confirmed": True,
              "source": inspect_image(source), "layers": layers,
              "uncovered_bbox": uncovered.getbbox(),
              "limitations": ["No semantic AI segmentation or hidden-area reconstruction.",
                              "Overlapping or soft masks may change composite appearance.",
                              "No rigging, physics simulation, PSD or Cubism model export."]}
    (out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

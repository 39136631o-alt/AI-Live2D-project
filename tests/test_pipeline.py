import json
import subprocess
import sys

import pytest
from PIL import Image, ImageChops

from live2d_pipeline.pipeline import inspect_image, load_image, process


@pytest.fixture
def artwork(tmp_path):
    source = tmp_path / "source.png"
    image = Image.new("RGBA", (4, 2), (200, 100, 50, 255))
    image.putpixel((0, 0), (10, 20, 30, 128))
    image.save(source)
    entries = []
    for name, pixels in [("Head", [255, 255, 0, 0] * 2), ("Body", [0, 0, 255, 255] * 2)]:
        mask = Image.new("L", image.size)
        mask.putdata(pixels)
        mask.save(tmp_path / f"{name}.png")
        entries.append({"name": name, "mask": f"{name}.png"})
    spec = tmp_path / "layers.json"
    spec.write_text(json.dumps({"schema_version": 1, "rights_confirmed": True, "layers": entries}))
    return source, spec, tmp_path / "out"


def test_roundtrip_and_provenance(artwork):
    source, spec, out = artwork
    result = process(source, spec, out)
    assert Image.open(out / "preview.png").tobytes() == Image.open(source).tobytes()
    assert result["cubism_model"] is False
    assert len(result["source"]["sha256"]) == 64
    assert result["uncovered_bbox"] is None
    assert json.loads((out / "manifest.json").read_text())["layers"][1]["order"] == 1
    with pytest.raises(FileExistsError):
        process(source, spec, out)


@pytest.mark.parametrize("change", ["rights", "duplicate", "unsafe", "empty", "version"])
def test_invalid_manifest_leaves_no_output(artwork, change):
    source, spec, out = artwork
    data = json.loads(spec.read_text())
    if change == "rights": data["rights_confirmed"] = False
    if change == "duplicate": data["layers"][1]["name"] = "head"
    if change == "unsafe": data["layers"][0]["name"] = "../escape"
    if change == "empty": data["layers"] = []
    if change == "version": data["schema_version"] = 2
    spec.write_text(json.dumps(data))
    with pytest.raises(ValueError): process(source, spec, out)
    assert not out.exists()


@pytest.mark.parametrize("mode,size", [("L", (2, 2)), ("RGB", (4, 2))])
def test_bad_mask(artwork, mode, size):
    source, spec, out = artwork
    Image.new(mode, size).save(spec.parent / "Head.png")
    with pytest.raises(ValueError): process(source, spec, out)
    assert not out.exists()


def test_soft_mask_preserves_source_alpha(artwork):
    source, spec, out = artwork
    Image.new("L", (4, 2), 128).save(spec.parent / "Head.png")
    process(source, spec, out)
    assert Image.open(out / "layers/000_Head.png").getpixel((0, 0))[3] == 64


def test_image_limits_and_corruption(artwork, monkeypatch):
    source, _, _ = artwork
    monkeypatch.setattr("live2d_pipeline.pipeline.MAX_PIXELS", 2)
    with pytest.raises(ValueError): load_image(source)
    source.write_text("not an image")
    with pytest.raises(OSError): inspect_image(source)


def test_cli_error_and_success(artwork):
    source, spec, out = artwork
    success = subprocess.run([sys.executable, "-m", "live2d_pipeline.cli", "layers",
                              str(source), str(spec), str(out)], capture_output=True, text=True)
    assert success.returncode == 0, success.stderr
    assert json.loads(success.stdout)["artifact_type"] == "image_layer_intermediate"
    failure = subprocess.run([sys.executable, "-m", "live2d_pipeline.cli", "inspect",
                              str(out / "missing")], capture_output=True, text=True)
    assert failure.returncode == 2
    assert "error:" in failure.stderr


def test_empty_visible_layer_rejected(artwork):
    source, spec, out = artwork
    Image.new("L", (4, 2), 0).save(spec.parent / "Head.png")
    with pytest.raises(ValueError, match="empty visible layer"):
        process(source, spec, out)
    assert not out.exists()


def test_exif_orientation(tmp_path):
    path = tmp_path / "rotated.png"
    image = Image.new("RGB", (3, 2), "red")
    exif = Image.Exif()
    exif[274] = 6
    image.save(path, exif=exif)
    assert load_image(path).size == (2, 3)
    assert inspect_image(path)["warnings"]


def test_animated_image_rejected(tmp_path):
    path = tmp_path / "animated.gif"
    Image.new("RGB", (2, 2), "red").save(path, save_all=True,
        append_images=[Image.new("RGB", (2, 2), "blue")], duration=100, loop=0)
    with pytest.raises(ValueError, match="animated"):
        load_image(path)

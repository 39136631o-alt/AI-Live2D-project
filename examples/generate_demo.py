"""Generate original geometric artwork and disjoint masks; no external assets."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw


def generate(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    source = Image.new("RGBA", (128, 128))
    draw = ImageDraw.Draw(source)
    draw.ellipse((24, 16, 104, 96), fill=(240, 190, 150, 255))
    draw.rectangle((32, 97, 96, 127), fill=(70, 130, 210, 255))
    source.save(out / "character.png")
    layers = []
    for name, box in [("PartHead", (0, 0, 127, 96)), ("PartBody", (0, 97, 127, 127))]:
        mask = Image.new("L", source.size)
        ImageDraw.Draw(mask).rectangle(box, fill=255)
        mask.save(out / f"{name}.png")
        layers.append({"name": name, "mask": f"{name}.png"})
    (out / "layers.json").write_text(json.dumps({"schema_version": 1,
        "rights_confirmed": True, "layers": layers}, indent=2) + "\n")


if __name__ == "__main__":
    generate(sys.argv[1])

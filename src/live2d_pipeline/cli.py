import argparse
import json
import sys

from PIL import Image

from .pipeline import inspect_image, process


def main():
    parser = argparse.ArgumentParser(description="Prepare image layers; does not generate Cubism models")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("inspect")
    check.add_argument("image")
    extract = commands.add_parser("layers")
    extract.add_argument("image")
    extract.add_argument("specification")
    extract.add_argument("output")
    args = parser.parse_args()
    try:
        result = (inspect_image(args.image) if args.command == "inspect" else
                  process(args.image, args.specification, args.output))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, Image.DecompressionBombError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

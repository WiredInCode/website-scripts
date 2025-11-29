'''
Inline Images in HTML File
-------------------------------------------------------------------------------

This script scans an HTML file for <img> tags and replaces their `src`
attributes with base64-encoded data URIs, producing a fully self-contained
HTML file for easy sharing. 

Features:
    • Supports both local image files and remote HTTP/HTTPS image URLs
    • Handles PNG, JPG/JPEG, GIF, WEBP, SVG, and most other image formats
    • Automatically detects MIME types (with sensible fallbacks)
    • Gracefully handles missing local files and HTTP download errors

Usage:
    python inline_images.py /path/to/input.html
        → Produces "input-inlined.html"

    python inline_images.py input.html -o output.html
        → Saves output to a custom file

Arguments:
    input.html        Path to the HTML file to process
    -o, --output      Optional output filename

Dependencies:
    - Python standard library: argparse, base64, mimetypes, pathlib, re
    - Third-party: BeautifulSoup4 (bs4), requests

Output:
    A new HTML file with all <img> tags inlined as base64 data URIs.
'''

import argparse
import base64
from bs4 import BeautifulSoup
import mimetypes
from pathlib import Path
import re
import requests


def clean_path(src: str) -> str:
    # Remove file URI prefixes
    if src.startswith("file:\\") or src.startswith("file:/"):
        src = re.sub(r"^file:[/\\]*", "", src)
    return src


def read_remote_image(url: str) -> bytes | None:
    # Fetch an image from the web; return bytes or None if failed
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"⚠️ WARNING: Failed to download {url}: {e}")
        return None


def read_local_image(path: Path) -> bytes | None:
    # Read a local image file; return bytes or None if missing.
    if not path.exists():
        print(f"⚠️ WARNING: Local image not found: {path}")
        return None

    try:
        return path.read_bytes()
    except Exception as e:
        print(f"⚠️ WARNING: Failed to read {path}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Inline all <img> tags in an HTML file as base64 data URIs."
    )
    parser.add_argument("input_file", help="Path to the HTML file to process")
    parser.add_argument("-o", "--output", help="Output HTML file name")

    args = parser.parse_args()

    html_path = Path(args.input_file)
    if not html_path.exists():
        print(f"❌ Error: Input file not found: {html_path}")
        return

    # Default output name: <input>-inlined.html
    output_path = (
        Path(args.output)
        if args.output
        else html_path.with_name(html_path.stem + "-inlined.html")
    )

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src.startswith("data:"):
            continue

        clean_src = clean_path(src)

        # Decide if remote or local
        is_remote = clean_src.startswith("http://") or clean_src.startswith("https://")

        if is_remote:
            data = read_remote_image(clean_src)
        else:
            data = read_local_image(Path(clean_src))

        if data is None:
            continue  # Skip image on errors

        # Determine MIME type
        mime, _ = mimetypes.guess_type(clean_src)
        mime = mime or "image/png"

        # Encode and inline
        encoded = base64.b64encode(data).decode("utf-8")
        img["src"] = f"data:{mime};base64,{encoded}"

    output_path.write_text(str(soup), encoding="utf-8")
    print(f"✅ Done! Saved as {output_path}")


if __name__ == "__main__":
    main()

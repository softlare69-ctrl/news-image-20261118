"""Entry program for the make.fun news-image-20261118 bounty.

This program bundles a newspaper front-page image (entry.png) and copies
it byte-for-byte to the output directory as ``entry.png``.

Behaviour:
  * The output directory is taken from the ``MAKEFUN_OUTPUT_DIR``
    environment variable when it is set and non-empty, and defaults
    to ``/output`` otherwise.
  * The bundled ``entry.png`` next to this script must exist and must
    really be a PNG (checked via its 8-byte magic header).
  * The copy is written atomically: it goes to a temporary file in the
    output directory first, is verified by comparing the SHA-256 hashes
    of source and destination, and is then renamed into place.
  * On success the destination path, byte size and SHA-256 are printed.

Standard library only. No network access. Fully deterministic.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

# The 8-byte PNG signature defined by the PNG specification.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Name of the bundled image and of the output file.
IMAGE_NAME = "entry.png"

# Fallback output directory when MAKEFUN_OUTPUT_DIR is unset or empty.
DEFAULT_OUTPUT_DIR = "/output"


def resolve_output_dir() -> Path:
    """Return the directory the entry image should be written to."""
    override = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if override:
        return Path(override)
    return Path(DEFAULT_OUTPUT_DIR)


def bundled_image_path() -> Path:
    """Return the path of the image bundled next to this script."""
    return Path(__file__).resolve().parent / IMAGE_NAME


def sha256_of(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_is_png(path: Path) -> None:
    """Raise a clear error unless the file starts with the PNG magic.

    The check reads only the first eight bytes, so a file that merely
    ends in ``.png`` but contains something else is rejected with the
    offending bytes shown, rather than being copied silently.
    """
    with path.open("rb") as handle:
        header = handle.read(len(PNG_MAGIC))
    if header != PNG_MAGIC:
        raise ValueError(
            f"{path} is not a PNG image: first {len(PNG_MAGIC)} bytes "
            f"are {header.hex() or '(empty)'} but a PNG must start with "
            f"the magic {PNG_MAGIC.hex()}"
        )


def copy_atomically(source: Path, destination: Path) -> None:
    """Copy *source* to *destination* via a temp file, verified by hash.

    The data is written to a temporary file in the destination's
    directory, the copy's SHA-256 is compared against the source's, and
    only then is the temporary file renamed into place, so the final
    file is either complete and identical or not there at all.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = sha256_of(source)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=".entry-", delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            with source.open("rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    temp_file.write(chunk)

        actual = sha256_of(temp_path)
        if actual != expected:
            raise IOError(
                f"copy verification failed for {destination}: "
                f"copied sha256 {actual} != source sha256 {expected}"
            )

        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def main() -> int:
    """Copy the bundled image to the output directory and report it."""
    source = bundled_image_path()
    if not source.is_file():
        print(
            f"error: bundled image not found: {source}",
            file=sys.stderr,
        )
        return 1

    try:
        check_is_png(source)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_dir = resolve_output_dir()
    destination = output_dir / IMAGE_NAME

    try:
        copy_atomically(source, destination)
    except (OSError, IOError) as exc:
        print(f"error: failed to write {destination}: {exc}", file=sys.stderr)
        return 1

    size = destination.stat().st_size
    digest = sha256_of(destination)
    print(f"destination: {destination}")
    print(f"bytes: {size}")
    print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

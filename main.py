#!/usr/bin/env python3
"""Entry program for the make.fun news-image bounty.

Copies the bundled front-page image (entry.png, sitting next to this
script) byte-for-byte to the grader's output directory, as entry.png.

The output directory is taken from the MAKEFUN_OUTPUT_DIR environment
variable when it is set and non-empty, and defaults to /output.

The copy is a plain direct copy: no temporary file is created inside
the output folder, so nothing about the output directory's contents or
the resulting file's permissions is left to chance. After copying, the
destination is explicitly made world-readable (mode 0644) and the copy
is verified by comparing SHA-256 hashes of the source and destination.

Standard library only, no network access, fully deterministic.
"""

import hashlib
import os
import shutil
import stat
import sys
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
OUTPUT_FILENAME = "entry.png"
OUTPUT_MODE = 0o644


def fail(message: str) -> "SystemExit":
    """Abort with a clear error on stderr and a non-zero exit code."""
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def bundled_image_path() -> Path:
    """Return the path of entry.png bundled next to this script."""
    return Path(__file__).resolve().parent / OUTPUT_FILENAME


def output_directory() -> Path:
    """Return the output directory from the environment, or /output."""
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if env_dir.strip():
        return Path(env_dir)
    return Path("/output")


def check_png_magic(source: Path) -> None:
    """Fail unless the source file starts with the PNG magic header."""
    try:
        with source.open("rb") as handle:
            header = handle.read(len(PNG_MAGIC))
    except OSError as exc:
        raise fail(f"cannot read bundled image {source}: {exc}") from exc
    if header != PNG_MAGIC:
        raise fail(
            f"bundled image {source} is not a PNG "
            f"(bad magic header: {header!r})"
        )


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_image(source: Path, destination: Path) -> None:
    """Copy source directly to destination, then make it world-readable.

    shutil.copyfile performs a plain byte-for-byte copy with no
    temporary file. The destination's mode is then set explicitly to
    0644 so the grader (or any other user) can read the output, even
    when this program runs under a different uid.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Remove any stale destination first: a leftover read-only file
    # would otherwise make the copy fail on a re-run into the same dir.
    if destination.exists():
        destination.unlink()
    shutil.copyfile(source, destination)
    os.chmod(destination, OUTPUT_MODE)


def main() -> int:
    source = bundled_image_path()
    if not source.is_file():
        print(f"error: bundled image not found: {source}", file=sys.stderr)
        return 1

    check_png_magic(source)

    destination = output_directory() / OUTPUT_FILENAME
    try:
        copy_image(source, destination)
    except OSError as exc:
        print(f"error: failed to write output {destination}: {exc}",
              file=sys.stderr)
        return 1

    source_hash = sha256_of(source)
    destination_hash = sha256_of(destination)
    if source_hash != destination_hash:
        print(
            f"error: SHA-256 mismatch after copy: "
            f"source {source_hash} != destination {destination_hash}",
            file=sys.stderr,
        )
        return 1

    mode = stat.S_IMODE(os.stat(destination).st_mode)
    if mode != OUTPUT_MODE:
        print(
            f"error: output mode is {mode:04o}, expected {OUTPUT_MODE:04o}",
            file=sys.stderr,
        )
        return 1

    print(f"wrote {destination} (sha256 {destination_hash}, mode 0644)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

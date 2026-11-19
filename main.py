"""Entry for make.fun bounty "news-image-20261118" — the world on
Wednesday, 18 November 2026, summed up in one front-page image.

Copies the bundled front-page image (entry.png) to the output path,
byte-for-byte. The output directory honours MAKEFUN_OUTPUT_DIR when the
harness sets it, and defaults to /output. No network access; fully
deterministic (two runs produce identical bytes), and the copy is
verified with SHA-256 before the program reports success.
"""

import hashlib
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
DST = os.path.join(OUT_DIR, "entry.png")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        raise SystemExit("bundled image missing: %s" % SRC)
    os.makedirs(OUT_DIR, exist_ok=True)
    shutil.copyfile(SRC, DST)
    src_hash = sha256(SRC)
    dst_hash = sha256(DST)
    if src_hash != dst_hash:
        raise SystemExit("copy mismatch: output differs from bundled image")
    print("Wrote %s (%d bytes, sha256 %s)"
          % (DST, os.path.getsize(DST), dst_hash))


if __name__ == "__main__":
    main()

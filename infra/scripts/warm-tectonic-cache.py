"""Run at Docker build time: compile the fixture resume once so every TeX package,
font map, and fontconfig cache the template needs is baked into the image layer.
After this, runtime compiles run with TECTONIC_ONLY_CACHED=1 and zero network."""

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, "/app")

from core.schemas import MasterResume  # noqa: E402
from latex.compile import compile_tex  # noqa: E402
from latex.render import render_tex  # noqa: E402

fixture = pathlib.Path("/app/latex/tests/fixtures/sample_master.json")
master = MasterResume(**json.loads(fixture.read_text()))
tex = render_tex(master, None)

# First compile: downloads the bundle into TECTONIC_CACHE_DIR.
pdf_path, log = compile_tex(tex, timeout_s=600)
if not pdf_path:
    print(log, file=sys.stderr)
    sys.exit("cache warm-up compile failed")

# Second compile must succeed fast and fully offline.
os.environ["TECTONIC_ONLY_CACHED"] = "1"
start = time.time()
pdf_path, log = compile_tex(tex, timeout_s=60)
elapsed = time.time() - start
if not pdf_path:
    print(log, file=sys.stderr)
    sys.exit("offline verification compile failed — cache is incomplete")
print(f"cache warmed; offline compile took {elapsed:.2f}s")

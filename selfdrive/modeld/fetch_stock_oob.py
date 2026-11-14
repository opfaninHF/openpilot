"""Fetch the stock artifacts built for the 1112 tinygrad revision."""
import hashlib
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = "/datasets/sunnypilot/sunnypilot_models_v1/resolve/main/models/defaults/"
MODELS = {
  "drive": ("small/model-CD210-1aa3a430-121/driving_cd210_tinygrad.pkl",
            "6398a4b0e474eac003280599cef701cd01c670a42c0d74c7df72583bfc923329"),
  "dm": ("dm/model-dmonitoring_model-(October-21,-2026)-1aa3a430-122/dmonitoring_model_tinygrad.pkl",
         "acefa66802a7b02bb4ee485725e5b5eb2e96522a3a82ff8efc83dad7568926fc"),
}


def fetch(key: str, target: Path) -> None:
  path, expected = MODELS[key]
  target.parent.mkdir(parents=True, exist_ok=True)
  partial = target.with_suffix(".part")
  failures = []
  for host in ("huggingface.co", "hf-mirror.com"):
    try:
      digest = hashlib.sha256()
      with urlopen(f"https://{host}{ROOT}{path}", timeout=30) as response, partial.open("wb") as output:
        while block := response.read(1024 * 1024):
          digest.update(block)
          output.write(block)
      if digest.hexdigest() != expected:
        raise ValueError("SHA-256 mismatch")
      partial.replace(target)
      return
    except (OSError, ValueError) as exc:
      failures.append(f"{host}: {exc}")
      partial.unlink(missing_ok=True)
  raise RuntimeError(f"Cannot fetch verified {key} artifact: {'; '.join(failures)}")


if __name__ == "__main__":
  fetch(sys.argv[1], Path(sys.argv[2]))

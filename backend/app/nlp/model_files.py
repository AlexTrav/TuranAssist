import hashlib
import sys
import urllib.request
from pathlib import Path

from ..config import MODEL_CACHE_DIR, MODEL_FILES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_path(name: str) -> Path:
    return MODEL_CACHE_DIR / name


# скачивает энкодер и токенизатор с зафиксированных коммитов Hugging Face и сверяет SHA-256;
# уже скачанный файл с верной суммой повторно не качается
def fetch_all() -> None:
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, spec in MODEL_FILES.items():
        path = local_path(name)
        if path.exists() and sha256(path) == spec["sha256"]:
            print(f"{name}: уже есть")
            continue
        url = f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{spec['path']}"
        print(f"{name}: скачиваю {url}")
        with urllib.request.urlopen(url, timeout=300) as resp, path.open("wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        actual = sha256(path)
        if actual != spec["sha256"]:
            path.unlink()
            sys.exit(f"{name}: контрольная сумма не совпала ({actual})")
        print(f"{name}: {path.stat().st_size / 2**20:.1f} МБ, SHA-256 совпадает")


if __name__ == "__main__":
    fetch_all()

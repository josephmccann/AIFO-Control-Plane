import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name):
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if name.startswith("mission-"):
        constitution = ROOT / "docs/engineering-os/ENGINEERING_CONSTITUTION.md"
        if constitution.exists():
            import hashlib

            digest = hashlib.sha256(constitution.read_bytes()).hexdigest()
            value["eos"]["constitution_sha256"] = digest
    return value

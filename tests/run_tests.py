from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TmpPathFixture:
    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        return Path(self._tmp.name)

    def __exit__(self, exc_type, exc, tb) -> None:
        self._tmp.cleanup()


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    passed = 0
    for path in sorted(ROOT.glob("test_*.py")):
        module = _load(path)
        for name in dir(module):
            if not name.startswith("test_"):
                continue
            test = getattr(module, name)
            if not callable(test):
                continue
            if "tmp_path" in test.__code__.co_varnames[: test.__code__.co_argcount]:
                with TmpPathFixture() as tmp_path:
                    test(tmp_path)
            else:
                test()
            passed += 1
    print(f"{passed} tests passed")


if __name__ == "__main__":
    main()

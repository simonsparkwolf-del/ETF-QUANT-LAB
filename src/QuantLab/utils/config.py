from pathlib import Path


def _find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".project-root").exists():
            return p
    raise RuntimeError("找不到 .project-root，无法确定项目根目录")


def get_db_path() -> Path:
    """Return the canonical datapool database path."""
    return _find_project_root(Path(__file__)) / "data" / "datapool.db"


def load_pathes() -> dict:
    ROOT = _find_project_root(Path(__file__))
    return {
        "ROOT": ROOT,
        "data": ROOT / "data",
        "model": ROOT / "model",
        "reports": ROOT / "reports",
        "research": ROOT / "research",
    }


if __name__ == "__main__":
    print(load_pathes())
    print(get_db_path())

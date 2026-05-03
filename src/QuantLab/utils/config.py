from pathlib import Path

def load_pathes() -> dict:
    def find_project_root(start: Path | None = None) -> Path:
        start = (start or Path.cwd()).resolve()
        layer = 0
        for p in [start, *start.parents]:
            if (p / ".project-root").exists():
                return p
            layer += 1
            if layer > 5:
                break
        raise RuntimeError("找不到 .project-root，无法确定项目根目录")
    ROOT = find_project_root(Path(__file__))
    config = {"ROOT": ROOT,
    "data": ROOT / "data",
    "model": ROOT / "model",
    "reports": ROOT / "reports",
    "research":ROOT / "research"}
    return config
if __name__ == "__main__":
    config = load_pathes()
    print(config)
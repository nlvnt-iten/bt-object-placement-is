from pathlib import Path
import shutil

class FileCopyService:
    def copy(self, src: str | Path, dst: str | Path) -> None:
        src = Path(src).expanduser().resolve()
        dst = Path(dst).expanduser().resolve()

        if src == dst:
            return

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[FILE] copied {src} → {dst}")

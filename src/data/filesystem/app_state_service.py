from __future__ import annotations
import threading, os, sys
from pathlib import Path

from data.utils import AppStateConverter
from data.models import AppState


class AppStateService:
    def __init__(
        self,
        state_dir: Path | str | None = None,
        filename: str = "application_state.json",
    ):
        if state_dir is None:
            if getattr(sys, "frozen", False):
                entry_dir = Path(sys.executable).resolve().parent
            else:
                entry_dir = Path(sys.modules["__main__"].__file__).resolve().parent
            state_dir = entry_dir / "state"

        self._state_dir = Path(state_dir)
        self._state_file = self._state_dir / filename

    def _ensure_dirs(self):
        if not self._state_dir.exists():
            os.makedirs(self._state_dir, exist_ok=True)

    def save_async(self, app_state: AppState, cb = None) -> threading.Thread:
        def _writer():
            try:
                self._ensure_dirs()
                json_text = AppStateConverter.to_json(app_state)
                self._state_file.write_text(json_text, encoding="utf-8")
                print(f"[STATE] saved → {self._state_file}")
                if cb: cb(app_state)
            except Exception as e:
                print(f"[STATE] save failed: {e}")
                if cb: cb(None)

        t = threading.Thread(target=_writer, daemon=True)
        t.start()
        return t

    def load_async(self, callback) -> threading.Thread:
        def _reader():
            try:
                if not self._state_file.exists():
                    print("[STATE] no file to load")
                    callback(None)
                    return
                text = self._state_file.read_text(encoding="utf-8")
                app_state = AppStateConverter.from_json(text)
                callback(app_state)
            except Exception as e:
                print(f"[STATE] load failed: {e}")
                callback(None)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        return t
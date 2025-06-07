from presentation.config import kivi_config

from functools import partial
from pathlib import Path
from copy import deepcopy

from kivy.app            import App
from kivy.core.window    import Window
from kivy.clock          import Clock

from osmnx import settings as ox_settings
ox_settings.use_cache = True
ox_settings.log_console = False

from data.filesystem import AppStateService, FileCopyService
from data.models import AppState

from .main_layout import MainLayout
from .placement_graph_view_model import PlacementGraphVM

class ObjectPlacementApp(App):
    AUTOSAVE_SEC = 10.0

    def build(self):
        self.title = "Object Placement Determinator"
        Window.maximize() 

        self._vm = PlacementGraphVM()
        self._state_service = AppStateService()
        self._file_copy_service = FileCopyService()

        self._state_service.load_async(self._on_state_loaded)

        Clock.schedule_interval(
            partial(self._autosave, self._vm, self._state_service),
            ObjectPlacementApp.AUTOSAVE_SEC,
        )

        return MainLayout(self._vm)

    def _on_state_loaded(self, app_state: AppState | None):
        
        def _cb():
            print("ObjectPlacementApp: state loaded")
            if app_state:
                app_state.to_vm(self._vm)

        Clock.schedule_once(lambda _: _cb())

    @staticmethod
    def _autosave(vm: PlacementGraphVM, svc: AppStateService, *_):
        print("ObjectPlacementApp: Autosave called by timer / on_stop event")
        return svc.save_async(AppState.from_vm(vm))

    def on_stop(self):
        print("ObjectPlacementApp: on_stop event")
        t = self._autosave(self._vm, self._state_service)
        t.join()

    def export_state(self, destination_path: str | Path) -> None:
        state = deepcopy(AppState.from_vm(self._vm))

        def _cb(_):
            self._file_copy_service.copy(self._state_service._state_file,
                                         Path(destination_path))

        self._state_service.save_async(state, _cb)

    def import_state(self, source_path: str | Path) -> None:
        self._file_copy_service.copy(Path(source_path),
                                     self._state_service._state_file)
        self._state_service.load_async(self._on_state_loaded)
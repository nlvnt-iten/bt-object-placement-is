from math import log2, ceil
from operator import itemgetter
import networkx as nx
from functools import partial

from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.scrollview   import ScrollView
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.button       import Button
from kivy.uix.textinput    import TextInput
from kivy.uix.label        import Label
from kivy.uix.slider       import Slider
from kivy.uix.scrollview   import ScrollView
from kivy.core.window      import Window
from kivy.clock            import Clock
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup        import Popup
from kivy.uix.filechooser  import FileChooserIconView
from kivy.app              import App

from algorithms.distance_resolvers.distance_resolvers_enum import DistanceResolverType

import presentation.config.constants as pconstants
from presentation.placement_graph_view_model import PlacementGraphVM
from presentation.components.list_rows import EdgeRow, NodeRow, FilledNodeRow, ObjectTypeRow
from presentation.views.map_view import BoundedGraphMapView

class MainLayout(BoxLayout):
    def __init__(self, vm : PlacementGraphVM, **kw):
        super().__init__(orientation='horizontal', **kw)
        self._vm = vm

        sidebar_scroll = ScrollView(size_hint_x=None, width=pconstants.SIDEBAR_WIDTH,
                                    bar_width=8, scroll_type=['bars'],
                                    bar_inactive_color=[.7, .7, .7, .9],
                                    bar_color=[.7, .7, .7, .9], effect_cls='ScrollEffect')
        sidebar = BoxLayout(orientation='vertical', spacing=6,
                            padding=[6, 6, 16, 6], size_hint_y=None)
        sidebar.bind(minimum_height=sidebar.setter('height'))
        sidebar_scroll.add_widget(sidebar)
        
        status_box = BoxLayout(orientation='vertical', size_hint_y=None)
        status_box.bind(minimum_height=status_box.setter('height'))

        title_label = Label(
            text='Статус',
            padding=[0, 12, 0, 0],
            size_hint=(1, None),
            height=26,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )
        title_label.bind(size=lambda *x: setattr(title_label, 'text_size', title_label.size))

        self.status_label = Label(
            text='',
            size_hint_y=None,
            font_size='13sp',
            padding=[0, 12, 0, 0],
            color=(0, 1, 0, 1),
            halign='center',
            valign='middle'
        )

        self.status_label.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None))
        )

        self.status_label.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )

        self.status_label.height = self.status_label.texture_size[1]
        self.status_label.width = self.status_label.width

        def _update_status_label(*_):
            if 'message' in vm.status:
                self.status_label.text = vm.status['message'] if isinstance(vm.status['message'], str) else ""
            if 'status' in vm.status and vm.status['status'] \
                and not vm.status['status'] == PlacementGraphVM.OperationStatus.IN_PROGRESS:
                if vm.status['status'] == PlacementGraphVM.OperationStatus.SUCCESS:
                    self.status_label.color = (0, 1, 0, 1)
                elif vm.status['status'] == PlacementGraphVM.OperationStatus.FAILURE:
                    self.status_label.color = (1, 0, 0, 1)
            else:
                self.status_label.color = (1, 1, 1, 1)
        self._vm.bind(status=_update_status_label)

        status_box.add_widget(title_label)
        status_box.add_widget(self.status_label)
        sidebar.add_widget(status_box)

        top_btn_row = BoxLayout(size_hint_y=None, height=40, spacing=6)
        export_btn  = Button(text="Експорт")
        import_btn  = Button(text="Імпорт")
        export_btn.size_hint_x = import_btn.size_hint_x = .5
        top_btn_row.add_widget(export_btn)
        top_btn_row.add_widget(import_btn)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=12))
        sidebar.add_widget(top_btn_row, index=0)
        sidebar.add_widget(BoxLayout(size_hint_y=None, height=8))

        export_btn.bind(on_release=lambda *_: self._show_export_dialog())
        import_btn.bind(on_release=lambda *_: self._show_import_dialog())

        self.pnetwork_efficiency_label=Label(text="Коеф. загальної ефективності розміщення: N/A",
                                             size_hint_y=None,height=20,color=(1,1,1,1), padding=[0, 12, 0, 0])
        self._vm.bind(overall_placement_efficiency=lambda _, x: self.pnetwork_efficiency_label.setter('text')(self.pnetwork_efficiency_label,f"Коеф. загальної ефективності розміщення: {f'{x:.2f}' if x is not None else 'N/A'}"))

        sidebar.add_widget(self.pnetwork_efficiency_label)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=12))

        self.type_name_input = TextInput(hint_text='Тип об’єкта(ів) для розміщення',
                                         multiline=False, size_hint_y=None, height=40)
        self.type_name_input.bind(text=self._limit_label_length)
        sidebar.add_widget(self.type_name_input)

        selector_box = BoxLayout(size_hint_y=None, height=32, spacing=4)

        minus_btn = Button(text='‑', size_hint_x=None, width=40)
        plus_btn  = Button(text='+', size_hint_x=None, width=40)
        self.count_label = Label(text='1', size_hint_x=None, width=40,
                                 color=(1, 1, 1, 1))

        self.coeff_input = TextInput(text='', multiline=False,
                                     input_filter='float', hint_text="Коефіцієнт внеску",
                                     size_hint_x=1)
        selector_box.add_widget(minus_btn)
        selector_box.add_widget(self.count_label)
        selector_box.add_widget(plus_btn)
        selector_box.add_widget(self.coeff_input)
        sidebar.add_widget(selector_box)

        plus_btn.bind(on_release=lambda *_: self._update_count(1))
        minus_btn.bind(on_release=lambda *_: self._update_count(-1))

        add_btn = Button(text='Додати об’єкти', size_hint_y=None, height=40,
                         disabled=vm.incoming_request_blocked)
        add_btn.bind(on_release=lambda *_: self._add_objects_of_type())
        vm.bind(incoming_request_blocked=add_btn.setter('disabled'))
        sidebar.add_widget(add_btn)

        label_scroll = ScrollView(size_hint_y=None, height=150, bar_width=8,
                                  scroll_type=['bars', 'content'], effect_cls='ScrollEffect')
        self.object_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        self.object_box.bind(minimum_height=self.object_box.setter('height'))
        label_scroll.add_widget(self.object_box)
        sidebar.add_widget(label_scroll)
        self._vm.bind(placement_object_types=self._update_placement_objects_list)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=20))

        self.inp_a=TextInput(hint_text='Точка розміщення A',input_filter='int',multiline=False,size_hint_y=None,height=40)
        self.inp_b=TextInput(hint_text='Точка розміщення B',input_filter='int',multiline=False,size_hint_y=None,height=40)
        add_edge_btn=Button(text='Додати зв\'язок розміщення',size_hint_y=None,height=40, disabled=vm.incoming_request_blocked)
        add_edge_btn.bind(on_release=self._add_edge)
        vm.bind(incoming_request_blocked=add_edge_btn.setter("disabled"))
        sidebar.add_widget(self.inp_a)
        sidebar.add_widget(self.inp_b)
        sidebar.add_widget(add_edge_btn)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=12))

        nodes_scroll=ScrollView(size_hint_y=None,height=150,bar_width=8,effect_cls='ScrollEffect')
        edges_scroll=ScrollView(size_hint_y=None,height=150,bar_width=8,effect_cls='ScrollEffect')
        self.node_box=BoxLayout(orientation='vertical',size_hint_y=None,spacing=6)
        self.edge_box=BoxLayout(orientation='vertical',size_hint_y=None,spacing=2)
        self.node_box.bind(minimum_height=self.node_box.setter('height'))
        self.edge_box.bind(minimum_height=self.edge_box.setter('height'))
        nodes_scroll.add_widget(self.node_box)
        edges_scroll.add_widget(self.edge_box)
        sidebar.add_widget(Label(text="Точки розміщення:",size_hint_y=None,height=20,color=(1,1,1,1)))
        sidebar.add_widget(nodes_scroll)
        sidebar.add_widget(Label(text="Зв’язки розміщення:",size_hint_y=None,height=20,color=(1,1,1,1)))
        sidebar.add_widget(edges_scroll)
        self._vm.bind(graph=self._update_placement_point_list)
        self._vm.bind(graph=self._update_placement_link_list)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=24))

        self.d_label=Label(text="Щільність понад MST: 0.50",
                           size_hint_y=None,height=20,color=(1,1,1,1))
        self.d_label_extra=Label(text="Вручну додані зв'язки не враховуються",
                                 size_hint_y=None,height=20,color=(1,1,1,1),
                                 font_size=14)
        self.slider=Slider(min=0,max=1,value=0.5,step=0.01,size_hint_y=None,height=40)
        self.slider.bind(value=lambda s,v: self.d_label.setter('text')(self.d_label,f"Щільність понад MST: {v:.2f}"))
        self._vm.bind(minimum_density=self.slider.setter('min'))
        sidebar.add_widget(self.d_label)
        sidebar.add_widget(self.d_label_extra)
        sidebar.add_widget(self.slider)

        compute_graph_btn = Button(text='Обчислити MST (стандарт/розшир.)',
                                   size_hint_y=None, height=40,
                                   disabled=vm.incoming_request_blocked)
        vm.bind(incoming_request_blocked=compute_graph_btn.setter("disabled"))
        compute_graph_btn.bind(on_release=lambda *_: self._vm.compute_mst_links(self.slider.value))
        sidebar.add_widget(compute_graph_btn)

        switch_box = BoxLayout(size_hint_y=None, height=32)

        geo_btn  = ToggleButton(text='Географічна відстань',   group='dist', allow_no_selection=False)
        road_btn = ToggleButton(text='Відстань за дорогами', group='dist', allow_no_selection=False)

        def _update_distance_resolver_type(*_):
            geo_btn.state = 'down' if self._vm.distance_resolver_type == DistanceResolverType.GEODETIC else 'normal'
            road_btn.state = 'down' if self._vm.distance_resolver_type == DistanceResolverType.ROADNETWORK else 'normal'
        _update_distance_resolver_type()

        vm.bind(distance_resolver_type=_update_distance_resolver_type)

        def _set_dr_on_activated(type, state):
            if state == 'down':
                self._vm.set_distance_resolver_type(type)

        geo_btn.bind(state=lambda _, value: _set_dr_on_activated(DistanceResolverType.GEODETIC, value))
        road_btn.bind(state=lambda _, value: _set_dr_on_activated(DistanceResolverType.ROADNETWORK, value))
        switch_box.add_widget(geo_btn)
        switch_box.add_widget(road_btn)
        sidebar.add_widget(switch_box)

        graph_manager_box = BoxLayout(size_hint_y=None, height=40)

        clear_edges_btn   = Button(text='Очистити зв\'язки',
                                   size_hint_x=.33,
                                   disabled=vm.incoming_request_blocked)
        clear_graph_btn   = Button(text='Очистити мережу',
                                   size_hint_x=.33,
                                   disabled=vm.incoming_request_blocked)
        
        clear_edges_btn.bind(on_release=lambda *_: self._vm.clear_placement_links())
        clear_graph_btn.bind(on_release=lambda *_: self._vm.clear_placement_network())

        vm.bind(incoming_request_blocked=clear_edges_btn.setter("disabled"))
        vm.bind(incoming_request_blocked=clear_graph_btn.setter("disabled"))

        graph_manager_box.add_widget(clear_edges_btn)
        graph_manager_box.add_widget(clear_graph_btn)

        sidebar.add_widget(graph_manager_box)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=32))

        self.penalty_label = Label(
            text="Штраф суміжних однотипних об'єктів: 0%",
            size_hint_y=None,
            height=20,
            color=(1, 1, 1, 1)
        )
        self.penalty_slider = Slider(
            min=0.0,
            max=1.0,
            value=0.0,
            step=0.01,
            size_hint_y=None,
            height=40
        )
        self.penalty_slider.bind(
            value=lambda s, v: self.penalty_label.setter('text')(
                self.penalty_label, f"Штраф суміжних однотипних об'єктів: {int(v * 100)}%")
        )

        def _on_slider_released(instance, touch):
            if touch.grab_current is instance:
                self._vm.set_adjacent_st_penalty(instance.value)

        self.penalty_slider.bind(on_touch_up=_on_slider_released)
        self._vm.bind(adjacent_st_penalty=lambda _, value: self.penalty_slider.setter('value')(
            self.penalty_slider, value
        ))
        
        sidebar.add_widget(self.penalty_label)
        sidebar.add_widget(self.penalty_slider)

        bottom_box = BoxLayout(size_hint_y=None, height=40)

        compute_btn = Button(text='Розрахувати розміщення',
                             size_hint_x=.5,
                             disabled=vm.incoming_request_blocked or not vm.compute_placement_allowed)
        clear_btn   = Button(text='Очистити розміщення',
                             size_hint_x=.5,
                             disabled=vm.incoming_request_blocked)
        clear_btn.bind(on_release=lambda *_: self._vm.clear_computed_placement())
        compute_btn.bind(on_release=lambda *_: self._vm.compute_placement())

        bottom_box.add_widget(compute_btn)
        bottom_box.add_widget(clear_btn)

        def _update_compute_btn_state(*_):
            compute_btn.disabled = vm.incoming_request_blocked or not vm.compute_placement_allowed
        vm.bind(incoming_request_blocked=_update_compute_btn_state, compute_placement_allowed=_update_compute_btn_state)


        vm.bind(incoming_request_blocked=clear_btn.setter('disabled'))

        sidebar.add_widget(bottom_box)

        sidebar.add_widget(BoxLayout(size_hint_y=None, height=24))

        self.add_widget(sidebar_scroll)

        self.g=nx.Graph() 
        self.map=BoundedGraphMapView(self._vm, remove_cb=self._vm.remove_node,
                                     add_cb=self._vm.add_node,lat=0,lon=0,zoom=1,size_hint=(1,1))
        self.add_widget(self.map)

        Window.bind(on_resize=self._update_zoom)
        Clock.schedule_once(lambda _:self._update_zoom(Window,Window.width,Window.height),0)

    def _add_objects_of_type(self):
        type_name = self.type_name_input.text.strip()
        if not type_name:
            return
        count = int(self.count_label.text)
        try:
            coeff = float(self.coeff_input.text)
        except ValueError:
            return

        result = self._vm.add_objects_of_type(type_name, count, coeff)

        if result:
            self.type_name_input.text = ""
            self.count_label.text = "1"
            self.coeff_input.text = ""

    def _add_edge(self, *_):
        try: 
            a_i, b_i = int(self.inp_a.text) - 1, int(self.inp_b.text) - 1
            nodes_list = sorted(list(self._vm.graph.nodes()))
            a, b = nodes_list[a_i], nodes_list[b_i]
            self._vm.add_edge(a, b)
        except:
            return

    def _update_count(self,delta):
        new=max(1,int(self.count_label.text)+delta)
        self.count_label.text=str(new)

    def _limit_label_length(self,inst,val):
        if len(val)>32: inst.text=val[:32]

    def _update_zoom(self,_w,w,h):
        min_z=max(ceil(log2(max(1,w-pconstants.SIDEBAR_WIDTH)/pconstants.TILE_SIZE)),
                  ceil(log2(max(1,h)/pconstants.TILE_SIZE)))
        self.map.set_min_zoom(min_z)

    def _update_placement_point_list(self, *_):
      self.node_box.clear_widgets([w for w in self.node_box.children if isinstance(w, NodeRow) or isinstance(w, FilledNodeRow)])

      sorted_nodes = sorted(list(self._vm.graph.nodes(data=True)), key=itemgetter(0))
      for i, node in enumerate(sorted_nodes):
         node_id, data = node[0], node[1]
         if 'placed_object_type' in data and 'placed_object_color' in data:
            self.node_box.add_widget(FilledNodeRow(i + 1,
                                                   data['lon'] if 'lon' in data else "N/A", 
                                                   data['lat'] if 'lat' in data else "N/A",
                                                   partial(self._vm.remove_node, node_id),
                                                   color=data['placed_object_color'],
                                                   object_type=data['placed_object_type'],
                                                   k=data['independent_contribution_rate'],
                                                   k_c=data['context_contribution_rate'] if 'context_contribution_rate' in data else None))
         else:
            self.node_box.add_widget(NodeRow(i + 1, 
                                             data['lon'] if 'lon' in data else "N/A", 
                                             data['lat'] if 'lat' in data else "N/A",
                                             partial(self._vm.remove_node, node_id)))
    
    def _update_placement_link_list(self, *_):
      self.edge_box.clear_widgets([w for w in self.edge_box.children if isinstance(w, EdgeRow)])

      nodes_list = list(self._vm.graph.nodes())
      sorted_edges_list = sorted(list(self._vm.graph.edges()))
      for a, b in sorted_edges_list:
          a_i, b_i = nodes_list.index(a), nodes_list.index(b)
          type = self._vm.graph[a][b]['type'] if 'type' in self._vm.graph[a][b] else None
          self.edge_box.add_widget(EdgeRow(a_i + 1, b_i + 1, type, partial(self._vm.remove_edge, a, b)))

    def _update_placement_objects_list(self, *_):
        self.object_box.clear_widgets([w for w in self.object_box.children
                                       if isinstance(w, ObjectTypeRow)])

        for obj_type, data in self._vm.placement_object_types.items():
            color = data['color']
            coeff = data['contribution_coeff']
            for j in range(data['count']):
                row_text = f"{obj_type} #{j + 1}"
                self.object_box.add_widget(
                    ObjectTypeRow(row_text, color, coeff,
                                  partial(self._vm.remove_objects_of_type,
                                          obj_type, 1)))

    def _show_export_dialog(self):
        from pathlib import Path
        import sys
        path = None
        if getattr(sys, "frozen", False):
            path = str(Path(sys.executable).resolve().parent)
        else:
            path = str(Path(sys.modules["__main__"].__file__).resolve().parent)
        
        chooser = FileChooserIconView(path=path, dirselect=True)
        filename_input = TextInput(text="placement_state.json",
                                   size_hint_y=None, height=30)

        def _update_filename_input(_, selection):
            if selection:
                filename_input.text = Path(selection[0]).name

        chooser.bind(selection=_update_filename_input)

        btn_save = Button(text="Експортувати", size_hint_y=None, height=40)
        btn_cancel = Button(text="Скасувати", size_hint_y=None, height=40)

        root = BoxLayout(orientation='vertical', spacing=6, padding=6)
        root.add_widget(chooser)
        root.add_widget(filename_input)
        buttons = BoxLayout(size_hint_y=None, height=40, spacing=6)
        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_save)
        root.add_widget(buttons)

        popup = Popup(title="Експортувати стан у ...", content=root,
                      size_hint=(0.9, 0.9))

        def _do_save(*_):
            folder = chooser.path
            fname = filename_input.text.strip() or "placement_state.json"
            if not fname.lower().endswith(".json"):
                fname += ".json"
            full_path = Path(folder) / fname
            popup.dismiss()
            App.get_running_app().export_state(full_path)

        btn_save.bind(on_release=_do_save)
        btn_cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _show_import_dialog(self):
        from pathlib import Path
        import sys
        path = None
        if getattr(sys, "frozen", False):
            path = str(Path(sys.executable).resolve().parent)
        else:
            path = str(Path(sys.modules["__main__"].__file__).resolve().parent)

        chooser = FileChooserIconView(path=path, filters=["*.json"])
        popup = Popup(title="Імпортувати стан з ...", content=chooser,
                      size_hint=(0.9, 0.9))

        def _on_choose(_, __, ___):
            if chooser.selection:
                path = chooser.selection[0]
                popup.dismiss()
                App.get_running_app().import_state(path)

        chooser.bind(on_submit=_on_choose)
        popup.open()


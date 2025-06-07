from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.graphics       import Color, Ellipse

import presentation.config.constants as pconstants

class EdgeRow(BoxLayout):
    def __init__(self,a,b,type,rm_cb,**kw):
        super().__init__(orientation='horizontal',size_hint_y=None,height=30,padding=[0,0,16,0],**kw)
        self.a,self.b=a,b
        lbl=Label(text=f"{a} <-> {b}{f' ({type})' if type and isinstance(type, str) else ''}",
                  color=(1,1,1,1)); lbl.bind(size=lambda *_: lbl.setter('text_size')(lbl,lbl.size))
        self.add_widget(lbl)
        btn=Button(text='×',size_hint_x=None,width=40); btn.bind(on_release=lambda *_: rm_cb()); self.add_widget(btn)

class NodeRow(BoxLayout):
    def __init__(self,nid, lon, lat, rm_cb, **kw):
        super().__init__(orientation='horizontal',size_hint_y=None,height=48,padding=[0,0,16,0],**kw)

        left_col = BoxLayout(orientation="vertical", spacing=0, size_hint_x=1)

        self.node_id=nid
        lbl=Label(text=f"Точка розміщення #{nid}",color=(1,1,1,1)); lbl.bind(size=lambda *_: lbl.setter('text_size')(lbl,lbl.size))
        left_col.add_widget(lbl)
    
        coords_label = Label(text=f"Дов.: {lon} | Шир.: {lat}", color=(1, 1, 1, 1),
                             halign="left", valign="middle", font_size=12)
        coords_label.bind(size=lambda *_: coords_label.setter("text_size")(coords_label, coords_label.size))
        left_col.add_widget(coords_label)

        self.add_widget(left_col)

        btn=Button(text='×',size_hint_x=None,width=40); btn.bind(on_release=lambda *_: rm_cb()); 
        self.add_widget(btn)

class FilledNodeRow(BoxLayout):
    def __init__(self, nid, lon, lat, rm_cb, *, color=None, object_type=None, k=None, k_c=None, **kw):
        super().__init__(orientation="horizontal",
                         size_hint_y=None, height=64,
                         padding=[0, 0, 16, 0], **kw)

        left_col = BoxLayout(orientation="vertical", spacing=0, size_hint_x=1)

        main_lbl = Label(text=f"Точка розміщення #{nid}", color=(1, 1, 1, 1),
                         halign="left", valign="middle")
        main_lbl.bind(size=lambda *_: main_lbl.setter("text_size")(main_lbl, main_lbl.size))
        left_col.add_widget(main_lbl)
        
        coords_label = Label(text=f"Дов.: {lon} | Шир.: {lat}", color=(1, 1, 1, 1),
                             halign="left", valign="middle", font_size=12)
        coords_label.bind(size=lambda *_: coords_label.setter("text_size")(coords_label, coords_label.size))
        left_col.add_widget(coords_label)

        if color is not None and object_type is not None:
            r, g, b = color
            sub = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=24, spacing=4, padding=[0, 3, 0, 0])

            with sub.canvas.before:
                Color(r, g, b, 1)
                circle = Ellipse(size=(pconstants.LABEL_CIRCLE_R * 1.4,
                                       pconstants.LABEL_CIRCLE_R * 1.4))
            def _update_circle(*_):
                circle.pos = (sub.x,
                              sub.y + sub.height / 2 - circle.size[1] / 2)
            sub.bind(pos=_update_circle, size=_update_circle)

            sub_lbl_text = f"{object_type}   |   K = {k:.2f}   |   K(c) = {k_c:.2f}" if k_c is not None else f"{object_type}   |   K = {k:.2f}"
            sub_lbl = Label(text=sub_lbl_text, color=(1, 1, 1, 1),
                            halign="left", valign="middle", padding=[40,0,0,0], font_size=14)
            sub_lbl.bind(size=lambda *_: sub_lbl.setter("text_size")(sub_lbl, sub_lbl.size))
            sub.add_widget(sub_lbl)

            left_col.add_widget(sub)

        self.add_widget(left_col)

        btn = Button(text="×", size_hint_x=None, width=40)
        btn.bind(on_release=lambda *_: rm_cb())
        self.add_widget(btn)

class ObjectTypeRow(BoxLayout):
    def __init__(self, text, color, coeff, rm_cb, **kw):
        super().__init__(orientation="horizontal",
                         size_hint_y=None, height=42,
                         padding=[0, 0, 16, 0], **kw)

        r, g, b = color
        with self.canvas.before:
            Color(r, g, b, 1)
            self.circle = Ellipse(size=(pconstants.LABEL_CIRCLE_R * 2,
                                        pconstants.LABEL_CIRCLE_R * 2))
        self.bind(pos=self._update_circle, size=self._update_circle)

        lbl_box = BoxLayout(orientation="vertical", spacing=0)

        main_lbl = Label(text=text,
                         color=(1, 1, 1, 1),
                         halign="left", valign="middle",
                         padding=[40, 0, 0, 0])
        main_lbl.bind(size=lambda *_: main_lbl.setter("text_size")(main_lbl, main_lbl.size))

        k_lbl = Label(text=f"Коефіцієнт внеску = {coeff}",
                      font_size="11sp",
                      color=(1, 1, 1, 1),
                      padding=[40, 0, 0, 0],
                      halign="left", valign="middle")
        k_lbl.bind(size=lambda *_: k_lbl.setter("text_size")(k_lbl, k_lbl.size))

        lbl_box.add_widget(main_lbl)
        lbl_box.add_widget(k_lbl)
        self.add_widget(lbl_box)

        btn = Button(text="×", size_hint_x=None, width=40)
        btn.bind(on_release=lambda *_: rm_cb())
        self.add_widget(btn)

    def _update_circle(self, *_):
        self.circle.pos = (self.x,
                           self.y + self.height / 2 - pconstants.LABEL_CIRCLE_R)

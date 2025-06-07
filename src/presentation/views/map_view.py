from operator import itemgetter

from kivy_garden.mapview import MapView, MapLayer
from kivy.graphics       import Color, Ellipse, Line, Rectangle
from kivy.core.text      import Label as CoreLabel

import presentation.config.constants as pconstants
import presentation.utils.unit_conversion as puc


class GraphLayer(MapLayer):
    def __init__(self, g, remove_node_fun, add_node_fun, **kw): 
        super().__init__(**kw)
        self._remove_node_fun=remove_node_fun
        self._add_node_fun=add_node_fun
        self._g = g

    def reposition(self):
        if not self.parent:
            return
        
        mv=self.parent
        self.canvas.clear()
        with self.canvas:
            Color(.9,.2,.2,.9)
            for u,v in self._g.edges:
                lat1,lon1=self._g.nodes[u]['lat'],self._g.nodes[u]['lon']
                lat2,lon2=self._g.nodes[v]['lat'],self._g.nodes[v]['lon']
                x1,y1=mv.get_window_xy_from(lat1,lon1,mv.zoom)
                x2,y2=mv.get_window_xy_from(lat2,lon2,mv.zoom)
                Line(points=[x1,y1,x2,y2],width=2)
            for i, node in enumerate(sorted(self._g.nodes(data=True), key=itemgetter(0))):
                d = node[1]
                lat,lon=d['lat'],d['lon']
                x,y=mv.get_window_xy_from(lat,lon,mv.zoom)

                r, g, b = 0.1, 0.4, 1
                type_text = None
                if 'placed_object_color' in d and 'placed_object_type' in d and \
                    d['placed_object_color'] is not None and \
                    d['placed_object_type'] is not None:
                    r, g, b = d['placed_object_color']
                    type_text = str(d['placed_object_type'])
                
                Color(r, g, b, .9)

                Ellipse(pos=(x-pconstants.NODE_RADIUS,y-pconstants.NODE_RADIUS),
                        size=(pconstants.NODE_RADIUS*2,pconstants.NODE_RADIUS*2))
                lbl=CoreLabel(text=str(i + 1),font_size=14,color=(1,1,1,1))
                lbl.refresh()
                tw,th=lbl.texture.size
                Color(1,1,1,1)
                Rectangle(texture=lbl.texture,pos=(x-tw/2,y-th/2),size=(tw,th))

                if type_text:
                    type_lbl = CoreLabel(text=type_text, font_size=12, color=(0, 0, 0, 1))
                    type_lbl.refresh()
                    tw2, th2 = type_lbl.texture.size
                    Rectangle(texture=type_lbl.texture,
                              pos=(x - tw2 / 2, y + pconstants.NODE_RADIUS + 4),
                              size=(tw2, th2))

    def on_right_click(self, touch):
        if not self.parent:
            return

        mv=self.parent
        for n, d in list(self._g.nodes(data=True)):
            nx,ny=mv.get_window_xy_from(d['lat'],d['lon'],mv.zoom)
            if (touch.x-nx)**2+(touch.y-ny)**2 <= pconstants.NODE_RADIUS**2:
                self._remove_node_fun(n)
                self.reposition()
                return
        
        xl,yl=mv.to_widget(*touch.pos,relative=True)
        lat,lon=mv.get_latlon_at(xl,yl)
        self._add_node_fun(lat, lon)

class BoundedGraphMapView(MapView):
    def __init__(self, vm, **kw):
        _remove_cb=kw.pop('remove_cb')
        _add_cb=kw.pop('add_cb')
        super().__init__(**kw)
        
        self.layer, self._min_z = GraphLayer(vm.graph, _remove_cb, _add_cb), 0
        self.add_layer(self.layer)

        def _update_graph_layer(*_):
            self.layer._g=vm.graph
            self.layer.reposition()
        vm.bind(graph=_update_graph_layer)

        self.bind(zoom=self._keep_min,on_map_relocated=self._clamp)

    def set_min_zoom(self,z): 
        self._min_z=z
        self.zoom=max(self.zoom,z)

    def on_touch_down(self, t):
        if not self.collide_point(*t.pos) or t.button != 'right':
            return super().on_touch_down(t)
        
        if self.layer:
            self.layer.on_right_click(t)
            return True

    def _keep_min(self,*_):   
        self.zoom=max(self.zoom,self._min_z)

    def _clamp(self,*_):
        px,py=puc.latlon_to_pixel(self.lat,self.lon,self.zoom)
        w, h, world = self.width, self.height, pconstants.TILE_SIZE*2**self.zoom
        px=min(max(px,w/2),world-w/2)
        py=min(max(py,h/2),world-h/2)
        lat_c,lon_c=puc.pixel_to_latlon(px,py,self.zoom)
        if abs(lat_c-self.lat)>pconstants.EDGE_EPS or abs(lon_c-self.lon)>pconstants.EDGE_EPS:
            super().center_on(lat_c,lon_c)
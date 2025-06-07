from functools import wraps, partial
from enum import Enum
from copy import deepcopy

import networkx

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, AliasProperty, BooleanProperty, NumericProperty

from utils import GraphUtils

from algorithms.distance_resolvers import DistanceResolverType, GeodeticDistanceResolver, RoadNetworkDistanceResolver
from algorithms.pnetwork_builders import MSTPLinkBuilder
from algorithms.placement_solvers import AdjPenPlacementAlgorithmGreedy
from algorithms.placement_efficiency import PEffAdjPenDeterminator

from road_network.road_network_provider import RoadNetworkProvider

from presentation.utils.types_conversion import DomainTypeConverter

from presentation.utils.id_generator import IDGenerator
from presentation.utils.color_generator import UniqueColorGenerator
from presentation.utils.schedulers import UIBackgroundScheduler

class PlacementGraphVM(EventDispatcher):
    class OperationStatus(Enum):
        SUCCESS = 1
        FAILURE = 2
        IN_PROGRESS = 3
    class StatusType(Enum):
        COMPUTE_PLACEMENT_NOT_ALLOWED = 1

    _status = ObjectProperty({
        'status': None,
        'type': None,
        'operation': None,
        'message': None,
    })

    _incoming_request_blocked = BooleanProperty(True)

    _placement_graph = ObjectProperty(allownone=False)
    _placement_object_types = ObjectProperty({})

    _distance_resolver_type = ObjectProperty(DistanceResolverType.GEODETIC)

    # Adjacent same-type penalty
    _adjacent_st_penalty = NumericProperty(0.0, min=0.0, max=1.0)

    _overall_placement_efficiency = NumericProperty(None, min=0.0, allownone=True)

    def __init__(self):
        self._id_generator = IDGenerator()
        self._color_generator = UniqueColorGenerator()

        self._scheduler = UIBackgroundScheduler()

        self._mstp_link_builder = MSTPLinkBuilder()
        self._geodedic_dr = GeodeticDistanceResolver()
        self._road_network_dr = RoadNetworkDistanceResolver()

        self._rn_rpovider = RoadNetworkProvider()
        self._rn_should_be_updated = True

        self._adj_pen_placement_algorithm = AdjPenPlacementAlgorithmGreedy()
        self._p_eff_adj_pen_determinator = PEffAdjPenDeterminator()

        self._placement_graph = networkx.Graph()

        self._incoming_request_blocked = False

        self._compute_efficiency_blocked = False

        self.bind(distance_resolver_type=lambda *_: self._on_distance_resolver_type_changed())
        
        self._eff_on_graph_change_lm = lambda *_: self.compute_placement_efficiency()
        self.bind(graph=self._eff_on_graph_change_lm)
        self.bind(adjacent_st_penalty=lambda *_: self.compute_placement_efficiency())

    def _get_incoming_request_blocked(self):
        return self._incoming_request_blocked
    def _get_graph(self):
        return self._placement_graph
    def _get_placement_object_types(self):
        return self._placement_object_types
    def _get_minimum_density(self):
        return GraphUtils.get_min_density_connected_graph(self._placement_graph.number_of_nodes())
    def _get_compute_placement_allowed(self) -> bool:
        if self._placement_graph.number_of_nodes() > 0 and \
           networkx.is_connected(self._placement_graph) and \
           self._get_placement_objects_count() == self._placement_graph.number_of_nodes():
            if self._status['type'] == PlacementGraphVM.StatusType.COMPUTE_PLACEMENT_NOT_ALLOWED:
                self._set_status(None, None, None)
            return True
        else:
            self._set_status(PlacementGraphVM.OperationStatus.FAILURE,
                             "Розрахунок розміщення неможливий, бо:\n"
                             " - немає точок розміщення і/або\n"
                             " - мережа розміщення не зв’язна і/або\n"
                             " - кількість точок і об’єктів не збігається",
                             PlacementGraphVM.StatusType.COMPUTE_PLACEMENT_NOT_ALLOWED)
            return False
    def _get_distance_resolver_type(self):
        return self._distance_resolver_type
    def _get_status(self):
        return self._status
    def _get_adjacent_st_penalty(self):
        return self._adjacent_st_penalty
    def _get_overall_placement_efficiency(self):
        return self._overall_placement_efficiency
    def _get_should_compute_placement(self):
        if self._placement_graph.number_of_nodes() <= 0 or \
           not networkx.is_connected(self._placement_graph):
            return False
        
        placement_objects_count = sum(1 if (node_data.get('placed_object_type', None) is not None \
                                            and node_data.get('placed_object_color', None) is not None \
                                            and node_data.get('independent_contribution_rate', None) is not None) else 0 \
                                        for _, node_data in self._placement_graph.nodes(data=True))
        
        if placement_objects_count != self._placement_graph.number_of_nodes():
            return False
        
        return True
               
    
    status = AliasProperty(_get_status, None, bind=['_status'], cache=True)
    
    incoming_request_blocked = AliasProperty(_get_incoming_request_blocked, None,
                                             bind=['_incoming_request_blocked'], cache=True)
    compute_placement_allowed = AliasProperty(_get_compute_placement_allowed, None,
                                              bind=['graph', 'placement_object_types'], cache=True)

    minimum_density = AliasProperty(_get_minimum_density, None,
                                    bind=['graph'], cache=True,
                                    min=0.0, max=1.0)

    graph = AliasProperty(_get_graph, None, bind=['_placement_graph'], cache=True)
    placement_object_types = AliasProperty(_get_placement_object_types, None,
                                           bind=['_placement_object_types'], cache=True)
    
    distance_resolver_type = AliasProperty(_get_distance_resolver_type, None,
                                           bind=['_distance_resolver_type'], cache=True)
    
    adjacent_st_penalty = AliasProperty(_get_adjacent_st_penalty, None,
                                        bind=['_adjacent_st_penalty'], cache=True,
                                        min=0.0, max=1.0)
    
    overall_placement_efficiency = AliasProperty(_get_overall_placement_efficiency, None,
                                                 bind=['_overall_placement_efficiency'], cache=True,
                                                 min=0.0)
    
    _should_compute_placement = AliasProperty(_get_should_compute_placement, None,
                                              bind=['graph'], cache=True)
    
    def blockable(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._incoming_request_blocked:
                print(f"Request to '{func.__name__}' is blocked.")
                return False
            else:
                return func(self, *args, **kwargs)  
        return wrapper
    
    def synchronized_request(name : str):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                if self._incoming_request_blocked:
                    return False
                else:
                    result = func(self, *args, **kwargs)  
                    if result:
                        print(f"Blocked by {name}")
                        self._incoming_request_blocked = True
                        self._set_status(PlacementGraphVM.OperationStatus.IN_PROGRESS, 
                                         f"Операція '{name}' виконується ...",
                                         operation=name)
                    return result
            return wrapper
        return decorator
    
    def synchronized_response_handler(name : str):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                self._incoming_request_blocked = False
                result = func(self, *args, **kwargs)
                if self._status['operation'] == name or \
                   self._status['status'] != PlacementGraphVM.OperationStatus.IN_PROGRESS:
                    if result:
                        self._set_status(PlacementGraphVM.OperationStatus.SUCCESS, 
                                        f"Операція '{name}' виконана.")
                    else:
                        self._set_status(PlacementGraphVM.OperationStatus.FAILURE, 
                                        f"Операція '{name}' не виконана (помилка).")
                return result
            return wrapper
        return decorator

    def notify_graph_change(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  
            if result:       
                self.property("graph").dispatch(self)
            return result
        return wrapper
    
    def notify_placement_object_types_change(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  
            if result:       
                self.property("placement_object_types").dispatch(self)
            return result
        return wrapper

    @blockable
    @notify_graph_change
    def add_node(self, latitude, longitude):
        self._placement_graph.add_node(self._id_generator.generate(),
                                       lat=latitude, lon=longitude)
        return True
    
    @blockable
    @notify_graph_change
    def remove_node(self, node_id):
        if node_id in self._placement_graph:
            self._placement_graph.remove_node(node_id)
            return True
        else:
            return False

    @blockable
    @notify_graph_change
    def add_edge(self, node_a_id, node_b_id):
        if node_a_id != node_b_id \
           and node_a_id in self._placement_graph and node_b_id in self._placement_graph:
            if self._placement_graph.has_edge(node_a_id, node_b_id):
                self._placement_graph[node_a_id][node_b_id]['type'] = "Доданий вручну"
            else:
                self._placement_graph.add_edge(node_a_id, node_b_id, type="Доданий вручну")
            return True
        else:
            return False
    
    @blockable
    @notify_graph_change
    def remove_edge(self, node_a_id, node_b_id):
        if self._placement_graph.has_edge(node_a_id, node_b_id):
            self._placement_graph.remove_edge(node_a_id, node_b_id)
            return True
        else:
            return False
    
    @blockable
    @notify_placement_object_types_change
    def add_objects_of_type(self, object_type, count, contribution_coeff):
        if not isinstance(count, int) or count < 1 \
           or not isinstance(contribution_coeff, (int, float)) or contribution_coeff <= 0 \
           or not isinstance(object_type, str) or not object_type:
            return False

        if object_type not in self._placement_object_types:
            self._placement_object_types[object_type] = \
                {'color': self._color_generator.get_color(),
                 'count': 0, 'contribution_coeff': 0}
        self._placement_object_types[object_type]['count'] += count
        self._placement_object_types[object_type]['contribution_coeff'] = contribution_coeff
        return True
    
    @blockable
    @notify_placement_object_types_change
    def remove_objects_of_type(self, object_type, count=None):
        if not isinstance(object_type, str) or not object_type \
            or object_type not in self._placement_object_types \
            or (count is not None and (not isinstance(count, int) or count < 1)):
            return False
        
        if not count:
            self._color_generator.release_color(self._placement_object_types[object_type]['color'])
            del self._placement_object_types[object_type]
        else:
            self._placement_object_types[object_type]['count'] -= count
            if self._placement_object_types[object_type]['count'] <= 0:
                self._color_generator.release_color(self._placement_object_types[object_type]['color'])
                del self._placement_object_types[object_type]
        return True
    
    @blockable
    @notify_graph_change
    def clear_computed_placement(self):
        for node_id in self._placement_graph.nodes:
            if 'placed_object_color' in self._placement_graph.nodes[node_id]:
                del self._placement_graph.nodes[node_id]['placed_object_color']
            if 'placed_object_type' in self._placement_graph.nodes[node_id]:
                del self._placement_graph.nodes[node_id]['placed_object_type']
            if 'independent_contribution_rate' in self._placement_graph.nodes[node_id]:
                del self._placement_graph.nodes[node_id]['independent_contribution_rate']
            if 'context_contribution_rate' in self._placement_graph.nodes[node_id]:
                del self._placement_graph.nodes[node_id]['context_contribution_rate']
        self._overall_placement_efficiency = None
        return True
    
    @blockable
    @notify_graph_change
    def clear_placement_links(self):
        self._placement_graph.remove_edges_from(list(self._placement_graph.edges))
        return True
    
    @blockable
    @notify_graph_change
    def clear_placement_network(self):
        self._placement_graph.clear()
        self._overall_placement_efficiency = None
        return True
    
    @blockable
    def set_distance_resolver_type(self, distance_resolver_type : DistanceResolverType):
        print(f"Set to {distance_resolver_type.name}")
        if not isinstance(distance_resolver_type, DistanceResolverType):
            return False
        self._distance_resolver_type = distance_resolver_type
        return True
    
    @blockable
    def set_adjacent_st_penalty(self, penalty : float):
        if not isinstance(penalty, (int, float)) or penalty < 0 or penalty > 1:
            return False
        self._adjacent_st_penalty = penalty
        return True
    
    @blockable
    @synchronized_request(name="Обчислення MST")
    def compute_mst_links(self, required_density_over_mst=None):
        edges_to_remove = [edge for edge in self._placement_graph.edges(data=True) if edge[2].get('type', None) != 'Доданий вручну']
        _graph = deepcopy(self._placement_graph)
        _graph.remove_edges_from(edges_to_remove)

        self._mstp_link_builder.set_required_density(required_density_over_mst)

        def _request():
            if self._rn_should_be_updated \
               and isinstance(self._mstp_link_builder.get_distance_resolver(), RoadNetworkDistanceResolver):
                print("VM: Updating road network")
                
                try:
                    road_network, coords, radius = self._rn_rpovider.get_road_network_coverage(self._placement_graph,
                                                                                               1.0)
                except Exception as e:
                    print(f"Error creating road network graph: {e}")
                    return None

                self._mstp_link_builder.get_distance_resolver().set_road_network(
                    road_network, coords, radius
                )
            
            return self._mstp_link_builder.compute_placement_point_links(
                DomainTypeConverter.convert_graph_to_placement_network(_graph)
            )

        @PlacementGraphVM.synchronized_response_handler(name="Обчислення MST")
        def _on_compute_placement_point_links_completed(self, placement_network):
            try:
                self._update_graph(placement_network)
            except Exception as _:
                return False
            return True

        self._scheduler.schedule(_request,
                                 callback=partial(_on_compute_placement_point_links_completed, self))
        
        return True
        
    @blockable
    @synchronized_request(name="Обчислення розміщення")
    def compute_placement(self):
        if not self.compute_placement_allowed:
            return False

        self._adj_pen_placement_algorithm.set_penalty(self._adjacent_st_penalty)

        @PlacementGraphVM.synchronized_response_handler(name="Обчислення розміщення")
        def _on_compute_placement_completed(self, placement_network):
            try:
                self._update_graph(placement_network)
            except Exception as _:
                return False
            return True

        self._scheduler.schedule(partial(self._adj_pen_placement_algorithm.compute_placement,
                                         DomainTypeConverter.convert_graph_to_placement_network(
                                             self._placement_graph
                                         ),
                                         DomainTypeConverter.convert_placement_objects_dict(
                                             self._placement_object_types
                                         )),
                                 callback=partial(_on_compute_placement_completed, self))
        
        return True
        
    @blockable
    @synchronized_request(name="Обчислення ефективності розміщення")
    def compute_placement_efficiency(self):
        if not self._should_compute_placement:
            self.unbind(graph=self._eff_on_graph_change_lm)
            self.clear_computed_placement()
            self.bind(graph=self._eff_on_graph_change_lm)
            return False

        self.unbind(graph=self._eff_on_graph_change_lm)
        self._clear_placement_efficiency()
        self.bind(graph=self._eff_on_graph_change_lm)

        self._p_eff_adj_pen_determinator.set_penalty(self._adjacent_st_penalty)

        @PlacementGraphVM.synchronized_response_handler(name="Обчислення ефективності розміщення")
        def _on_compute_placement_efficiency_completed(self, result):
            try:
                result_rn, total_efficiency = result
                self.unbind(graph=self._eff_on_graph_change_lm)
                self._update_graph(result_rn)
                self.bind(graph=self._eff_on_graph_change_lm)
                self._overall_placement_efficiency = total_efficiency
            except Exception as _:
                return False
            return True

        self._scheduler.schedule(partial(self._p_eff_adj_pen_determinator.calculate_placement_efficiency,
                                         DomainTypeConverter.convert_graph_to_placement_network(
                                             self._placement_graph
                                         )),
                                 callback=partial(_on_compute_placement_efficiency_completed, self))
        
        return True

    def _get_placement_objects_count(self):
        return sum([self._placement_object_types[object_type]['count']
                    for object_type in self._placement_object_types])
    
    def _on_distance_resolver_type_changed(self):
        self._mstp_link_builder.set_distance_resolver(
            self._geodedic_dr if self._distance_resolver_type == DistanceResolverType.GEODETIC
            else self._road_network_dr if self._distance_resolver_type == DistanceResolverType.ROADNETWORK
            else MSTPLinkBuilder.get_distance_resolver()
        )

    def _set_status(self, status, message, type=None, operation=None):
        self._status['status'] = status
        self._status['message'] = message
        self._status['type'] = type
        self._status['operation'] = operation
        self.property("status").dispatch(self)

    def _update_graph(self, placement_network):
       graph = DomainTypeConverter.convert_placement_network_to_graph(placement_network)

       for node_id, data in graph.nodes(data=True):
           if 'placed_object_type' in data:
               if 'placed_object_color' in self._placement_graph.nodes[node_id] \
                    and 'placed_object_type' in self._placement_graph.nodes[node_id] \
                    and self._placement_graph.nodes[node_id]['placed_object_type'] == data['placed_object_type']:
                    graph.nodes[node_id]['placed_object_color'] = self._placement_graph.nodes[node_id]['placed_object_color']
               elif data['placed_object_type'] in self._placement_object_types:
                    graph.nodes[node_id]['placed_object_color'] = \
                        self._placement_object_types[data['placed_object_type']]['color']
               else:
                   del graph.nodes[node_id]['placed_object_type']
                   if 'context_contribution_rate' in data:
                        del graph.nodes[node_id]['context_contribution_rate']
                   if 'independent_contribution_rate' in data:
                        del graph.nodes[node_id]['independent_contribution_rate'] 

       self._placement_graph = graph

    @notify_graph_change
    def _clear_placement_efficiency(self):
        self._overall_placement_efficiency = None
        for node_id in self._placement_graph.nodes:
            if 'context_contribution_rate' in self._placement_graph.nodes[node_id]:
                del self._placement_graph.nodes[node_id]['context_contribution_rate']
        
        return True
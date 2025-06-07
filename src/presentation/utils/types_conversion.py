from typing import Dict, List

import networkx as nx

from models import PlacementPoint, PlacementPointID, PlacementObject, PlacementNetwork

class DomainTypeConverter:
    @staticmethod
    def convert_placement_network_to_graph(pnetwork: PlacementNetwork) -> nx.Graph:
        graph = nx.Graph()

        for node_id in pnetwork.get_graph().nodes(data=False):
            placement_point = pnetwork.get_placement_point_data(node_id)

            if placement_point:
                id = placement_point.get_id().get_value()
                lon, lat, _ = placement_point.get_coordinates()
                
                placement_object = placement_point.get_object()
                
                graph.add_node(
                    id,
                    lon=lon,
                    lat=lat,
                )

                if placement_object:
                    graph.nodes[id]['placed_object_type'] = placement_object.get_name()
                    graph.nodes[id]['independent_contribution_rate'] = placement_object.get_independent_contribution_rate()
                    if placement_object.get_context_contribution_rate() is not None:
                        graph.nodes[id]['context_contribution_rate'] = placement_object.get_context_contribution_rate()

        graph.add_edges_from(pnetwork.get_graph().edges(data=True))

        return graph
    
    @staticmethod
    def convert_graph_to_placement_network(graph: nx.Graph) -> PlacementNetwork:
        pnetwork = PlacementNetwork(graph)

        for node_id, data in pnetwork.get_graph().nodes(data=True):
            placement_point = PlacementPoint(
                id=PlacementPointID(node_id),
                longitude=data['lon'],
                latitude=data['lat']
            )

            if "placed_object_type" in data and "independent_contribution_rate" in data:
                placement_point.set_object(PlacementObject(
                    unique_name=data['placed_object_type'],
                    independent_contribution_rate=data['independent_contribution_rate'],
                    context_contribution_rate=data.get('context_contribution_rate', None)
                    )
                )
            
            pnetwork.set_placement_point_data(node_id, placement_point)

        return pnetwork
    
    @staticmethod
    def convert_placement_objects_dict(objects : Dict) -> List[PlacementObject]:
        result = []
        
        for key, value in objects.items():
            name = key
            count = value['count'] if 'count' in value else 0

            for _ in range(count):
                placement_object = PlacementObject(
                    unique_name=name,
                    independent_contribution_rate=value['contribution_coeff'] if 'contribution_coeff' in value else 0.0
                )
                result.append(placement_object)
            
        return result
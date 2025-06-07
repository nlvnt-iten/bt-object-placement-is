from data.models import AppState, EdgeAttr, NodeAttr
from dataclasses import asdict
import json

class AppStateConverter:
    @staticmethod
    def to_json(app_state: AppState) -> str:
        return json.dumps(
            asdict(app_state),
            default=lambda o: list(o) if isinstance(o, tuple) else o,
            indent=2,
        )

    @staticmethod
    def from_json(text: str) -> AppState:
        raw = json.loads(text)

        node_dict = {}
        for nid, nd in raw.get("placement_graph_nodes", {}).items():
            node_dict[int(nid)] = NodeAttr(**nd)

        edge_list = []
        for u, v, ed in raw.get("placement_graph_edges", []):
            edge_list.append((u, v, EdgeAttr(**ed)))

        raw["placement_graph_nodes"] = node_dict
        raw["placement_graph_edges"] = edge_list

        return AppState(**raw)
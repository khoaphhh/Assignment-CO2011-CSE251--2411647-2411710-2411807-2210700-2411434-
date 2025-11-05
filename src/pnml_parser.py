"""
Task 1: PNML Parser
Đọc file PNML và chuyển thành cấu trúc Petri net nội bộ.
"""

import xmltodict

def ensure_list(x):
    """Đảm bảo phần tử luôn là list"""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

class PetriNet:
    def __init__(self, places, transitions, arcs, initial_marking):
        self.places = places
        self.transitions = transitions
        self.arcs = arcs
        self.initial_marking = initial_marking

    def summary(self):
        print("Places:", self.places)
        print("Transitions:", self.transitions)
        print("Arcs:", self.arcs)
        print("Initial marking:", self.initial_marking)

def load_pnml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = xmltodict.parse(f.read())

    net = data["pnml"]["net"]

    # Parse places
    places = []
    initial_marking = {}
    for p in ensure_list(net.get("place")):
        pid = p["@id"]
        places.append(pid)
        mark = 0
        if "initialMarking" in p and "text" in p["initialMarking"]:
            mark = int(p["initialMarking"]["text"])
        initial_marking[pid] = mark

    # Parse transitions
    transitions = [t["@id"] for t in ensure_list(net.get("transition"))]

    # Parse arcs
    arcs = [(a["@source"], a["@target"]) for a in ensure_list(net.get("arc"))]

    # Consistency check
    all_nodes = set(places) | set(transitions)
    for src, tgt in arcs:
        if src not in all_nodes or tgt not in all_nodes:
            raise ValueError(f"Inconsistent arc ({src}->{tgt}): node not defined")

    print("✅ PNML loaded successfully.")
    return PetriNet(places, transitions, arcs, initial_marking)
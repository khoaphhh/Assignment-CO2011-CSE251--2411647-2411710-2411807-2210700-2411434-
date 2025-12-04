import os
import xmltodict
import sys

class PetriNet:
    def __init__(self):
        self.places = {}      # {id: {'name': str, 'initial': int}}
        self.transitions = {} # {id: name}
        self.arcs = []        # list of tuples (source_id, target_id)

    def parse_pnml(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                doc = xmltodict.parse(f.read())
        except Exception as e:
            print("Lỗi khi đọc file PNML:", e)
            return False

        net = doc['pnml']['net']

        pages = net.get('page', None)
        if pages is None:
            pages = [net]  # nếu không có thẻ <page> thì dùng <net>
        elif isinstance(pages, dict):
            pages = [pages]

        for page in pages:
            # Places
            if 'place' in page:
                places = page['place']
                if isinstance(places, dict): places = [places]
                for place in places:
                    if '@id' not in place:
                        continue                # thiếu @id -> bỏ qua
                    pid = place['@id']
                    pname = place.get('name', {}).get('text', pid)
                    
                    initial = 0                 # đọc initialMarking cho task 2
                    im_node = place.get('initialMarking', {})
                    if im_node and isinstance(im_node, dict):
                        try:
                            initial_text = im_node.get('text', '0')
                            initial = int(initial_text)
                        except (ValueError, TypeError):
                            initial = 0 
                    
                    self.places[pid] = {'name': pname, 'initial': initial}

            # Transitions
            if 'transition' in page:
                transitions = page['transition']
                if isinstance(transitions, dict):
                    transitions = [transitions]
                for trans in transitions:
                    if '@id' not in trans:
                        continue
                    tid = trans['@id']
                    tname = trans.get('name', {}).get('text', tid)
                    self.transitions[tid] = tname

            # Arcs
            if 'arc' in page:
                arcs = page['arc']
                if isinstance(arcs, dict):
                    arcs = [arcs]
                for arc in arcs:
                    if '@source' not in arc or '@target' not in arc:
                        continue                #arc thiếu source hoặc target
                    source = arc['@source']
                    target = arc['@target']
                    self.arcs.append((source, target))
        return True

    def check_consistency(self):
        place_ids = set(self.places.keys())
        trans_ids = set(self.transitions.keys())
        valid_nodes = place_ids | trans_ids        
        errors = []
        for src, tgt in self.arcs:      # kiểm tra missing nodes
            if src not in valid_nodes:
                errors.append(f"Arc source '{src}' trỏ đến một node không tồn tại.")
            if tgt not in valid_nodes:
                errors.append(f"Arc target '{tgt}' trỏ đến một node không tồn tại.")

        # kiểm tra lỗi ngữ nghĩa (place với place hoặc transition với transition)
        for src, tgt in self.arcs:
            if src in place_ids and tgt in place_ids:
                errors.append(f"Arc nối 2 place: '{src}' -> '{tgt}'")
            if src in trans_ids and tgt in trans_ids:
                errors.append(f"Arc nối 2 transition: '{src}' -> '{tgt}'")

        if errors:
            for e in errors:
                print(f"  - {e}")
            return False # Trả về False (thất bại)
        else:
            return True # Trả về True (thành công)

    def summary(self):
        print("Places:", self.places)
        print("Transitions:", self.transitions)
        print("Arcs:", self.arcs)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    file_path = sys.argv[1]
    petri = PetriNet()
    
    if petri.parse_pnml(file_path):
        petri.summary()
        
        if not petri.check_consistency():
            print("\nDừng chương trình: Mạng Petri không nhất quán (invalid).")
            sys.exit(1)
            
    else:
        print("\nDỪNG CHƯƠNG TRÌNH: Không thể phân tích file.")
        sys.exit(1)
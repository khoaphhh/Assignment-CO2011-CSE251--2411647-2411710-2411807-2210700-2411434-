import time
import sys
from pyeda.inter import bddvar, expr2bdd
from pyeda.boolalg.expr import expr
from pnml_parser import PetriNet

class SymbolicReachabilityPyEDA(PetriNet):
    def __init__(self):
        super().__init__()
        self.place_to_curr_var = {}  # p -> x
        self.place_to_next_var = {}  # p -> x'

    def check_symbolic_consistency(self):
        """
        Kiểm tra tính hợp lệ của mạng Petri cho symbolic analysis
        Trả về: (is_valid, error_messages)
        """
        errors = []
        
        # 1. Kiểm tra places
        if not self.places:
            errors.append("Mạng không có places nào")
        
        # 2. Kiểm tra transitions và arcs
        invalid_transitions = []
        for t_id in self.transitions:
            pre_places = {src for src, tgt in self.arcs if tgt == t_id}
            post_places = {tgt for src, tgt in self.arcs if src == t_id}
            
            # Kiểm tra input places có tồn tại không
            invalid_inputs = pre_places - set(self.places.keys())
            if invalid_inputs:
                invalid_transitions.append(f"Transition '{t_id}' có input places không tồn tại: {invalid_inputs}")
            
            # Kiểm tra output places có tồn tại không
            invalid_outputs = post_places - set(self.places.keys())
            if invalid_outputs:
                invalid_transitions.append(f"Transition '{t_id}' có output places không tồn tại: {invalid_outputs}")
        
        errors.extend(invalid_transitions)
        
        # 3. Kiểm tra arcs không hợp lệ
        invalid_arcs = []
        for src, tgt in self.arcs:
            # Kiểm tra arc từ place không tồn tại
            if src not in self.places and src not in self.transitions:
                invalid_arcs.append(f"Arc source '{src}' trỏ đến một node không tồn tại")
            
            # Kiểm tra arc đến place/transition không tồn tại
            if tgt not in self.places and tgt not in self.transitions:
                invalid_arcs.append(f"Arc target '{tgt}' trỏ đến một node không tồn tại")
            
            # Kiểm tra arc nối 2 places
            if src in self.places and tgt in self.places:
                invalid_arcs.append(f"Arc nối 2 place: '{src}' -> '{tgt}'")
            
            # Kiểm tra arc nối 2 transitions
            if src in self.transitions and tgt in self.transitions:
                invalid_arcs.append(f"Arc nối 2 transition: '{src}' -> '{tgt}'")
        
        # Loại bỏ các thông báo trùng lặp
        invalid_arcs = list(set(invalid_arcs))
        errors.extend(invalid_arcs)
        
        return len(errors) == 0, errors

    def setup_variables(self):
        """
        Tạo biến BDD trong PyEDA.
        """
        sorted_places = sorted(self.places.keys())
        for i, p in enumerate(sorted_places):
            self.place_to_curr_var[p] = bddvar(f'x_{p}')
            self.place_to_next_var[p] = bddvar(f'x_{p}_prime')

    def encode_initial_marking(self):
        """
        Mã hóa trạng thái ban đầu: M0(x)
        """
        if not self.places:
            return expr2bdd(expr(1))
        
        expr_str_parts = []
        for p, info in self.places.items():
            if info['initial'] > 0:
                expr_str_parts.append(f"x_{p}")
            else:
                expr_str_parts.append(f"~x_{p}")
        
        expr_str = " & ".join(expr_str_parts) # Noi cac phan tu bang toan tu &
        boolean_expr = expr(expr_str) # chuyen thanh bieu thuc boolean
        return expr2bdd(boolean_expr) # chuyen bieu thuc boolean sang BDD

    def encode_transition_relation(self):
        """
        Tạo quan hệ chuyển đổi R(x, x')
        """
        # Kiểm tra có transition hay không
        if not self.transitions:
            return expr2bdd(expr(0))
            
        transition_relations = []
        all_places = set(self.places.keys())

        # Duyệt qua từng transition và xác định input/output places
        for t_id in self.transitions:
            pre_places = {src for src, tgt in self.arcs if tgt == t_id}
            post_places = {tgt for src, tgt in self.arcs if src == t_id}

            # Bỏ qua transitions có input/output không hợp lệ
            invalid_inputs = pre_places - set(self.places.keys())
            invalid_outputs = post_places - set(self.places.keys())
            if invalid_inputs or invalid_outputs:
                continue

            conditions = []
            
            # Điều kiện INPUT
            for p in pre_places:
                conditions.append(f"x_{p}")
            
            # Điều kiện OUTPUT
            changed_places = pre_places | post_places
            
            for p in all_places:
                if p in post_places:
                    conditions.append(f"x_{p}_prime")
                elif p in pre_places and p not in post_places:
                    conditions.append(f"~x_{p}_prime")
            
            # Frame Condition
            unchanged_places = all_places - changed_places
            for p in unchanged_places:
                frame_condition = f"((x_{p} & x_{p}_prime) | (~x_{p} & ~x_{p}_prime))"
                conditions.append(frame_condition)
            
            if conditions:
                trans_expr_str = " & ".join(conditions)
                try:
                    trans_rel = expr(trans_expr_str)
                    transition_relations.append(trans_rel)
                except Exception as e:
                    continue

        # Identity Relation
        identity_conditions = []
        for p in all_places:
            identity_conditions.append(f"((x_{p} & x_{p}_prime) | (~x_{p} & ~x_{p}_prime))")
        
        if identity_conditions:
            identity_expr_str = " & ".join(identity_conditions)
            try:
                identity_rel = expr(identity_expr_str)
                transition_relations.append(identity_rel)
            except Exception as e:
                pass

        # Kết hợp tất cả transition relations
        if transition_relations:
            full_expr_parts = [f"({str(rel)})" for rel in transition_relations]
            full_expr_str = " | ".join(full_expr_parts)
            try:
                full_relation = expr(full_expr_str)
                return expr2bdd(full_relation)
            except Exception as e:
                return expr2bdd(identity_rel) if 'identity_rel' in locals() else expr2bdd(expr(0))
        
        return expr2bdd(expr(0))

    def bdd_to_readable_formula(self, bdd_expr):
        """
        Chuyển BDD thành công thức symbolic có thể đọc được
        """
        try:
            satisfy_points = list(bdd_expr.satisfy_all())
            
            if not satisfy_points:
                return "False"
            
            formulas = []
            for point in satisfy_points:
                conditions = []
                for p, var in self.place_to_curr_var.items():
                    if var in point and point[var]:
                        conditions.append(f"x_{p}")
                    else:
                        conditions.append(f"¬x_{p}")
                
                if conditions:
                    formula = " ∧ ".join(conditions)
                    formulas.append(f"({formula})")
            
            if formulas:
                return " ∨ ".join(formulas)
            else:
                return "False"
                
        except Exception as e:
            return f"Error: {str(e)}"

    def compute_reachable(self, return_formula=True):
        # Kiểm tra tính hợp lệ trước khi tính toán
        is_valid, error_messages = self.check_symbolic_consistency()
        
        if not is_valid:
            print("Mạng Petri không hợp lệ cho phân tích Symbolic:")
            for error in error_messages:
                print(f"  - {error}")
            
            if return_formula:
                return 0, 0.0, {
                    'initial': "INVALID NETWORK",
                    'transition': "INVALID NETWORK", 
                    'final': "INVALID NETWORK",
                    'iterations': 0,
                    'valid': False,
                    'errors': error_messages
                }
            else:
                return 0, 0.0

        self.setup_variables()
        
        current_set = self.encode_initial_marking()
        initial_count = int(current_set.satisfy_count())
        initial_formula = self.bdd_to_readable_formula(current_set)
        
        if not self.places:
            if return_formula:
                return 0, 0.0, {
                    'initial': "INVALID - No places",
                    'transition': "INVALID - No places", 
                    'final': "INVALID - No places",
                    'iterations': 0,
                    'valid': False
                }
            else:
                return 0, 0.0
        
        trans_relation = self.encode_transition_relation()
        trans_count = int(trans_relation.satisfy_count())
        
        # Symbolic BFS
        start_time = time.time()
        current_vars = list(self.place_to_curr_var.values())
        iteration = 0
        max_iterations = 20
        
        while iteration < max_iterations:
            iteration += 1
            current_count = int(current_set.satisfy_count())
            
            # Image Computation
            product = current_set & trans_relation
            product_count = int(product.satisfy_count())
            
            if product_count == 0:
                break
            
            next_states_prime = product.smoothing(current_vars)
            next_count = int(next_states_prime.satisfy_count())
            
            if next_count == 0:
                break
            
            # Đổi tên x' -> x
            next_states = expr2bdd(expr(0))
            satisfy_points = list(next_states_prime.satisfy_all())
            
            for point in satisfy_points:
                state_conditions = []
                for p in self.places.keys():
                    var_next = self.place_to_next_var[p]
                    if var_next in point and point[var_next]:
                        state_conditions.append(f"x_{p}")
                    else:
                        state_conditions.append(f"~x_{p}")
                
                if state_conditions:
                    state_expr_str = " & ".join(state_conditions)
                    try:
                        state_bdd = expr2bdd(expr(state_expr_str))
                        next_states = next_states | state_bdd
                    except Exception as e:
                        continue
            
            # Hợp với tập hiện tại
            new_set = current_set | next_states
            
            # Kiểm tra hội tụ
            if new_set.equivalent(current_set):
                break
                
            current_set = new_set
        
        end_time = time.time()
        duration = end_time - start_time
        
        final_count = int(current_set.satisfy_count())
        final_formula = self.bdd_to_readable_formula(current_set)
        
        if return_formula:
            return final_count, duration, {
                'initial': initial_formula,
                'transition': f"R(x,x')",
                'final': final_formula,
                'iterations': iteration,
                'valid': True
            }
        else:
            return final_count, duration

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python src/reachability_symbolic_pyeda.py <file.pnml>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    net = SymbolicReachabilityPyEDA()
    
    if net.parse_pnml(file_path):
        count, duration, formulas = net.compute_reachable(return_formula=True)
        
        if formulas.get('valid', True):
            print(f"✅ Task 3 (PyEDA) Hoàn thành.")
            print(f"   Tổng số trạng thái: {count}")
            print(f"   Thời gian: {duration:.4f}s")
            print(f"   Công thức symbolic:")
            print(f"      - Initial: M₀(x) = {formulas['initial']}")
            print(f"      - Final Reachable: F(x) = {formulas['final']}")
            print(f"      - Iterations: {formulas['iterations']}")
        else:
            print(f"❌ Task 3 (PyEDA) Thất bại: Mạng không hợp lệ")
    else:
        sys.exit(1)

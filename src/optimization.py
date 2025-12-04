from reachability_explicit import ReachabilityNet

class OptimizationReachability(ReachabilityNet):
    def optimize_marking(self, objective_weights):
        reachable_markings = self.bfs()
        if not reachable_markings:
            return None, 0, 0
        best_value = -float('inf')
        best_marking = None
        for marking in reachable_markings:
            curr = 0
            for p in self.places:
                weight = objective_weights.get(p, 1)
                curr += weight * marking[p]
            
            if curr > best_value:
                best_value = curr
                best_marking = marking

        return best_marking, best_value, len(reachable_markings)

    def print_result(self, objective_weights):
        import time
        start = time.time()

        marking, value, count = self.optimize_marking(objective_weights)
        duration = time.time() - start
        
        print("\n" + "="*50)
        print("KẾT QUẢ TỐI ƯU HÓA")
        print("="*50)
        print(f"File PNML: {self.filename if hasattr(self, 'filename') else 'Unknown'}")
        print(f"Hàm mục tiêu: {objective_weights}")
        print(f"Chế độ: Maximize")
        print(f"Số đánh dấu đạt được: {count}")
        print(f"Thời gian tính toán: {duration:.4f} giây")
        print("-"*50)
        
        if marking is None:
            print("Không tìm thấy đánh dấu nào!")
        else:
            print(f"Giá trị tối ưu: {value}")
            print("Đánh dấu tối ưu:")
            for p in sorted(marking):
                print(f"  {p}: {marking[p]}")
        print("="*50)


def parse_user_objective(places):
    print(f"\nCác place trong mạng: {sorted(places)}")
    print("Nhập hàm mục tiêu dạng 'p1=2 p3=-1 p4=5'")
    print("Hoặc nhấn ENTER để dùng mặc định: tất cả trọng số = 1")
    
    raw = input("Objective weights: ").strip()
    weights = {}
    
    if raw == "":
        for p in places:
            weights[p] = 1
        print(f"➡️  Objective function: maximize {weights}")
    else:
        parts = raw.split()
        
        for part in parts:
            if "=" not in part:
                print(f"⚠ Lỗi định dạng: '{part}'. Bỏ qua.")
                continue
            
            try:
                p, w_str = part.split("=", 1)
                w = int(w_str)
                weights[p] = w
            except ValueError:
                print(f"⚠ Lỗi: '{part}' không đúng định dạng. Bỏ qua.")
        
        print(f"➡️  Objective function: maximize {weights}")
    
    for p in places:
        if p not in weights:
            weights[p] = 0
    
    return weights


if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) < 2:
        print("Cú pháp: python optimization.py <file.pnml>")
        print("Ví dụ: python optimization.py my_network.pnml")
        sys.exit(1)
    if not os.path.exists(sys.argv[1]):
        print(f"❌ Lỗi: File '{sys.argv[1]}' không tồn tại!")
        sys.exit(1)
    
    print("⏳ Đang tải mạng Petri...")
    net = OptimizationReachability()
    net.parse_pnml(sys.argv[1])
    net.build_pre_post()
    
    print(f"✅ Đã tải: {sys.argv[1]}")
    print(f"  • Số place: {len(net.places)}")
    print(f"  • Số transition: {len(net.transitions)}")
    print(f"  • Số cung: {len(net.arcs)}")
    weights = parse_user_objective(net.places)
    print("\n⏳ Đang tính toán các đánh dấu đạt được và tìm giá trị tối ưu...")
    net.print_result(weights)
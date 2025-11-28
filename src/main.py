import os
import sys

from reachability_explicit import ReachabilityNet
from reachability_bdd import SymbolicReachabilityPyEDA

def test_file(file_path):
    filename = os.path.basename(file_path)
    print(f"\n{'='*20} Testing: {filename} {'='*20}")

    net = ReachabilityNet()

    # --- TASK 1: Parsing & Consistency Check ---
    print(f"-> [Task 1] Parsing {filename}...")
    if not net.parse_pnml(file_path):
        print("❌ Parsing thất bại. Bỏ qua file này.")
        return

    print("-> [Task 1] Summary:")
    net.summary()

    print("-> [Task 1] Checking Consistency...")
    if not net.check_consistency():
        print("❌ Mạng không nhất quán (Invalid). Dừng kiểm tra Task 2.")
        return
    else:
        print("✅ Task 1 Passed: Mạng hợp lệ.")

    print(f"\n-> [Task 2] Computing Reachability Graph (BFS)...")
    try:
        # Bước 1: Xây dựng cấu trúc pre/post để bắn transition
        net.build_pre_post()

        # Bước 2: Chạy BFS
        reachable_markings = net.bfs()
        explicit_count = len(reachable_markings)

        # Bước 3: Báo cáo kết quả
        count = len(reachable_markings)
        print(f"✅ Task 2 Completed.")
        print(f"   Tổng số trạng thái đạt được (Reachable Markings): {count}")
        
        # In chi tiết nếu số lượng nhỏ (tùy chọn)
        if count <= 20:
            print("   Danh sách các marking:")
            for idx, m in enumerate(reachable_markings):
                # Sắp xếp key để in cho đẹp
                sorted_m = dict(sorted(m.items()))
                print(f"    {idx+1}. {sorted_m}")
        else:
            print("   (Danh sách quá dài, ẩn chi tiết)")

    except Exception as e:
        print(f"❌ Lỗi khi chạy Task 2: {e}")

    print(f"\n[Task 3] Symbolic Reachability (BDD)...")
    try:
        # Khởi tạo đối tượng BDD
        sym_net = SymbolicReachabilityPyEDA()
        
        # Copy dữ liệu từ net (Task 1) sang sym_net
        sym_net.places = net.places
        sym_net.transitions = net.transitions
        sym_net.arcs = net.arcs
        
        # Chạy tính toán BDD
        bdd_count, bdd_time, formulas = sym_net.compute_reachable(return_formula=True)
        
        print(f"✅ Hoàn thành.")
        print(f"   Tổng số trạng thái (Symbolic): {bdd_count}")
        print(f"   Thời gian tính toán: {bdd_time:.4f} giây")
        print(f"   Công thức symbolic:")
        print(f"      - Initial Marking: {formulas['initial']}")
        print(f"      - Reachable Set: {formulas['final']}")
        print(f"      - Iterations: {formulas['iterations']}")
        
        # --- SO SÁNH KẾT QUẢ (chỉ khi network hợp lệ) ---
        if is_consistent and explicit_count > 0:
            print(f"\n[Validation]")
            if explicit_count == bdd_count:
                print(f"   ✅ KẾT QUẢ KHỚP NHAU! ({explicit_count})")
            else:
                print(f"   ⚠️ CẢNH BÁO: LỆCH KẾT QUẢ!")
                print(f"      Explicit: {explicit_count}")
                print(f"      Symbolic: {bdd_count}")
        else:
            print(f"\n[Validation]")
            print(f"   ⚠️ Không thể so sánh: Network không hợp lệ")
            
    except Exception as e:
        print(f"❌ Lỗi Task 3: {e}")

def main():

    current_dir = os.path.dirname(os.path.abspath(__file__))

    examples_dir = os.path.join(os.path.dirname(current_dir), "examples")
    


    for f in sorted(os.listdir(examples_dir)):
        if f.endswith(".pnml"):
            path = os.path.join(examples_dir, f)
            test_file(path)
    


if __name__ == "__main__":
    main()

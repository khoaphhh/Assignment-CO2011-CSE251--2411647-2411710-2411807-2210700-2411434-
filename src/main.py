import os
import sys
import time

from reachability_explicit import ReachabilityNet
from reachability_bdd import SymbolicReachabilityPyEDA
from ilp_deadlock import DeadlockDetector
from optimization import OptimizationReachability


# ==============================
# HÀM PARSE INPUT CỦA NGƯỜI DÙNG
# ==============================
def parse_objective_input(user_input, places):
    """
    Parse chuỗi người dùng nhập dạng:
       p1=2 p3=-1 p5=10
    Trả về dict: { "p1": 2, "p3": -1, "p5": 10 }
    """
    weights = {}

    if not user_input.strip():
        # Empty -> dùng mặc định: tất cả trọng số = 1
        return {p: 1 for p in places}

    parts = user_input.split()
    for part in parts:
        if "=" not in part:
            print(f"⚠️ Bỏ qua mục tiêu không hợp lệ: {part}")
            continue
        place, val = part.split("=")
        if place not in places:
            print(f"⚠️ Place '{place}' không tồn tại trong PNML -> bỏ qua")
            continue
        try:
            weights[place] = int(val)
        except:
            print(f"⚠️ Trọng số '{val}' không hợp lệ -> bỏ qua")

    return weights

def test_file(file_path):
    filename = os.path.basename(file_path)
    print(f"\n{'=' * 70}")
    print(f"Testing: {filename}")
    print(f"{'=' * 70}")

    net = ReachabilityNet()

    print(f"\n[Task 1] Parsing {filename}")
    if not net.parse_pnml(file_path):
        print("Parsing failed. Skipping this file.")
        return

    net.summary()

    is_consistent = net.check_consistency()

    if not is_consistent:
        print("Network is invalid. Skipping Task 2 but continuing with Task 3.")
        explicit_count = 0
    else:
        print("Task 1 Passed: Network is valid.")

        print(f"\n[Task 2] Computing Reachability Graph (BFS)")
        try:
            net.build_pre_post()
            reachable_markings = net.bfs()
            explicit_count = len(reachable_markings)

            print(f"   Total reachable states: {explicit_count}")

            if explicit_count <= 20:
                print("   Marking list:")
                for idx, m in enumerate(reachable_markings):
                    sorted_m = dict(sorted(m.items()))
                    print(f"    {idx + 1}. {sorted_m}")
            else:
                print("   (List too long, hidden)")

        except Exception as e:
            print(f"Task 2 Error: {e}")
            explicit_count = 0

    print(f"\n[Task 3] Symbolic Reachability (BDD)")
    try:
        sym_net = SymbolicReachabilityPyEDA()

        sym_net.places = net.places
        sym_net.transitions = net.transitions
        sym_net.arcs = net.arcs

        bdd_count, bdd_time, formulas = sym_net.compute_reachable(return_formula=True)

        print(f"   Total states (Symbolic): {bdd_count}")
        print(f"   Computation time: {bdd_time:.4f}s")
        print(f"   Symbolic formula:")
        print(f"      - Initial: {formulas['initial']}")
        print(f"      - Final: {formulas['final']}")
        #print(f"      - Iterations: {formulas['iterations']}")

        if is_consistent and explicit_count > 0:
            print(f"\n[Validation]")
            if explicit_count == bdd_count:
                print(f"   RESULTS MATCH ({explicit_count})")
            else:
                print(f"   WARNING: MISMATCH!")
                print(f"      Explicit: {explicit_count}")
                print(f"      Symbolic: {bdd_count}")
        else:
            print(f"\n[Validation]")
            print(f"   Cannot compare: Network invalid or Task 2 failed")

    except Exception as e:
        print(f"Task 3 Error: {e}")
        return

    print(f"\n[Task 4] Deadlock Detection (ILP + BDD)...")

    try:
        detector = DeadlockDetector(net, sym_net)

        dead_marking, elapsed_time, status_message = detector.detect_deadlock(max_attempts=20)

        print(f"Completed.")

        if dead_marking is not None:
            readable_marking = {
                net.places.get(place_id, {}).get('name', place_id): token_count
                for place_id, token_count in dead_marking.items() if token_count > 0
            }
            print(f"   Result: DEADLOCK FOUND")
            print(f"   Deadlock marking: {dict(sorted(readable_marking.items())) if readable_marking else '(empty)'}")
        else:
            print(f"   Result: NO DEADLOCK")
            print(f"   Reason: {status_message}")

        print(f"   Time: {elapsed_time:.4f}s")

    except Exception as error:
        print(f"Task 4 Error: {error}")

# --- TASK 5: Optimization ---
    if is_consistent:
        print(f"\n[Task 5] Optimization Over Reachable Markings...")

        try:
            opt_net = OptimizationReachability()
            opt_net.places = net.places
            opt_net.transitions = net.transitions
            opt_net.arcs = net.arcs
            opt_net.build_pre_post()

            # 🧠 YÊU CẦU NGƯỜI DÙNG NHẬP OBJECTIVE
            print("\nNhập hàm mục tiêu dạng 'p1=2 p3=-1 p4=5'")
            print("Hoặc nhấn ENTER để dùng mặc định: tất cả trọng số = 1")
            print(f"Các place trong mạng: {list(net.places.keys())}")

            user_input = input("Objective weights: ")

            weights = parse_objective_input(user_input, net.places)

            print(f"➡️  Objective function: maximize {weights}")

            start_time = time.time()
            optimal_marking, optimal_value, total_markings = opt_net.optimize_marking(weights)
            runtime = time.time() - start_time

            if optimal_marking is None:
                print("❌ Không tìm được marking tối ưu.")
            else:
                print(f"- Optimal value: {optimal_value}")
                print(f"- Optimal marking: {optimal_marking}")
                print(f"- Running time: {runtime:.6f}s")

        except Exception as e:
            print(f"❌ Lỗi Task 5: {e}")

    else:
        print("\n[Task 5] Skip optimization (network invalid)")


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    examples_dir = os.path.join(os.path.dirname(current_dir), "examples")

    print(f"Scanning directory: {examples_dir}\n")

    if not os.path.exists(examples_dir):
        print(f"Examples directory not found: {examples_dir}")
        return

    pnml_files = sorted([f for f in os.listdir(examples_dir) if f.endswith(".pnml")])

    if not pnml_files:
        print("No .pnml files found in examples directory")
        return

    print(f"Found {len(pnml_files)} PNML file(s).\n")

    for f in pnml_files:
        path = os.path.join(examples_dir, f)
        test_file(path)

    print(f"\n{'=' * 70}")
    print("All files processed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
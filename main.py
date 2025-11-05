import argparse
from src.pnml_parser import load_pnml

def main():
    parser = argparse.ArgumentParser(description="Petri Net Assignment - CO2011")
    parser.add_argument("--task", required=True, choices=["parse", "explicit", "symbolic", "ilp", "optimize"])
    parser.add_argument("--input", default="examples/simple_net.pnml")
    args = parser.parse_args()

    if args.task == "parse":
        net = load_pnml(args.input)
        net.summary()

    elif args.task == "explicit":
        from src.reachability_explicit import compute_explicit
        compute_explicit(args.input)

    elif args.task == "symbolic":
        from src.reachability_bdd import compute_bdd
        compute_bdd(args.input)

    elif args.task == "ilp":
        from src.ilp_deadlock import detect_deadlock
        detect_deadlock(args.input)

    elif args.task == "optimize":
        from src.optimization import optimize_reachability
        optimize_reachability(args.input)

if __name__ == "__main__":
    main()
import argparse
from core.engine import profiler, tracer, analyzer, comparison
import config

def main():
    parser = argparse.ArgumentParser(description="Profilovací nástroj pro ARM emulaci v QEMU")
    subparsers = parser.add_subparsers(dest="command", help="Dostupné příkazy")

    # Příkaz pro kompilaci
    build_parser = subparsers.add_parser("build", help="Vytvoří testovací binárku")
    build_parser.add_argument("--source", required=True, help="Cesta ke zdrojovému souboru")

    # Příkaz pro trasování
    trace_parser = subparsers.add_parser("trace", help="Spustí trasování binárky v QEMU")
    trace_parser.add_argument("--binary", required=True, help="Cesta k binárnímu souboru")

    # Příkaz pro analýzu logů
    analyze_parser = subparsers.add_parser("analyze", help="Analyzuje vygenerovaný log trasování")
    analyze_parser.add_argument("--log", required=True, help="Cesta k log souboru")

    # Příkaz pro porovnání logů
    compare_parser = subparsers.add_parser("compare", help="Porovná dva logy trasování")
    compare_parser.add_argument("--logs", nargs=2, required=True, help="Cesty k log souborům")

    args = parser.parse_args()

    if args.command == "build":
        profiler.build_binary(args.source)
    elif args.command == "trace":
        tracer.run_trace(args.binary)
    elif args.command == "analyze":
        analyzer.analyze_log(args.log)
    elif args.command == "compare":
        comparison.compare_logs(args.logs[0], args.logs[1])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

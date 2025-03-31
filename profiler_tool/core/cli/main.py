import argparse
from core.cli.function_preparation import prepare_function
from core.cli.trace_analysis import trace_analysis
from core.cli.comparison import compare_json_runs

def main():
    parser = argparse.ArgumentParser(description="CLI nástroj pro analýzu binárek.")
    subparsers = parser.add_subparsers(dest="command")

    # Výběr funkce a kompilace
    select_parser = subparsers.add_parser("prepare-function", help="Vyber funkci z .h souboru a kompiluj.")
    select_parser.add_argument("-H", "--header", required=False, help="Hlavičkový soubor .h")
    select_parser.add_argument("-c", "--source", required=False, help="Zdrojový soubor .c")
    select_parser.add_argument("-f", "--function", required=False, help="Název funkce pro výběr")
    select_parser.add_argument("--klee", action="store_true", help="Použít KLEE analýzu")

    # Spuštění trace
    trace_parser = subparsers.add_parser("trace-analysis", help="Spusť binárku, vytvoř trace.log a proveď analýzu")
    trace_parser.add_argument("-b", "--binary", help="Cesta k binárnímu souboru")
    trace_parser.add_argument("-f", "--file", help="Soubor obsahující sady parametrů (každý řádek = jedna sada)")

    # Porovnání běhů
    compare_parser = subparsers.add_parser("compare-runs", help="Porovnej běhy na základě JSON souborů")
    compare_parser.add_argument("-d", "--directory", help="Složka s JSON soubory")
    compare_parser.add_argument("-f", "--files", nargs="*", help="Seznam JSON souborů k porovnání")

    args = parser.parse_args()

    if args.command == "prepare-function":
        prepare_function(header_file=args.header, src_file=args.source, function_name=args.function, use_klee=args.klee)
    elif args.command == "trace-analysis":
        trace_analysis(args.binary, args.file)
    elif args.command == "compare-runs":
        compare_json_runs(folder=args.directory, files=args.files)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

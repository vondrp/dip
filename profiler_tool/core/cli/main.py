"""
CLI nástroj pro analýzu funkcí v jazyce C pomocí trace a konkolického testování.

Tento skript poskytuje několik příkazů pro:
- výběr a kompilaci funkce z hlavičkového a zdrojového souboru (`prepare-function`)
- spuštění programu s trasováním pomocí GDB a analýzou výstupu (`trace-analysis`)
- porovnání více běhů podle výstupních JSON souborů (`compare-runs`)
- analýzu funkcí pomocí nástroje KLEE pro konkolické testování (`prepare-klee`)
- kombinovanou analýzu s automatickým výběrem a trasováním funkce (`func-analysis`)

Použití:
    python cli.py <command> [volby]

Dostupné příkazy:
- prepare-function : Vybere funkci ze souboru, vygeneruje main a zkompiluje binárku
- trace-analysis   : Spustí binárku s parametry, vytvoří trace a provede analýzu
- compare-runs     : Porovná výstupy z několika analýz na úrovni instrukcí
- prepare-klee     : Spustí analýzu funkce pomocí nástroje KLEE
- func-analysis    : Spojí výběr funkce, její kompilaci a analýzu do jednoho kroku

Argumenty pro jednotlivé příkazy se zobrazí pomocí:
    python cli.py <command> --help
"""

import argparse
from core.cli.function_preparation import prepare_function, prepare_klee
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
    select_parser.add_argument("--main-mode", choices=["auto", "template", "own"], default="auto", help="Způsob generování main.c")
    select_parser.add_argument("--own-main-file", required=False, help="Cesta k vlastnímu main souboru pokud použijete --main-mode own")


    # Spuštění trace
    trace_parser = subparsers.add_parser("trace-analysis", help="Spusť binárku, vytvoř trace.log a proveď analýzu")
    trace_parser.add_argument("-b", "--binary", help="Cesta k binárnímu souboru")
    trace_parser.add_argument("-f", "--file", help="Soubor obsahující sady parametrů (každý řádek = jedna sada)")

    # Porovnání běhů
    compare_parser = subparsers.add_parser("compare-runs", help="Porovnej běhy na základě JSON souborů")
    compare_parser.add_argument("-d", "--directory", help="Složka s JSON soubory")
    compare_parser.add_argument("-f", "--files", nargs="*", help="Seznam JSON souborů k porovnání")

    # Pouze příprava pro KLEE - konkolické testování 
    klee_parser = subparsers.add_parser("prepare-klee", help="Analyzuj funkci konkolickým testováním s KLEE a získej ukázkové vstupy.")
    klee_parser.add_argument("-H", "--header", required=False, help="Hlavičkový soubor .h")
    klee_parser.add_argument("-c", "--source", required=False, help="Zdrojový soubor .c")
    klee_parser.add_argument("-f", "--function", required=False, help="Název funkce pro výběr")

    # Nový příkaz pro připravení funkce a následné spuštění trace analysis
    combined_parser = subparsers.add_parser("func-analysis", help="Vyber si funkci k analýze.")
    combined_parser.add_argument("-H", "--header", required=False, help="Hlavičkový soubor .h")
    combined_parser.add_argument("-c", "--source", required=False, help="Zdrojový soubor .c")
    combined_parser.add_argument("-f", "--function", required=False, help="Název funkce pro výběr")
    combined_parser.add_argument("--main-mode", choices=["auto", "template", "own"], default="auto", help="Způsob generování main.c")
    combined_parser.add_argument("--own-main-file", required=False, help="Cesta k vlastnímu main souboru pokud použijete --main-mode own")
    combined_parser.add_argument("--result-file", required=False, help="Cesta k výstupnímu JSON souboru")


    args = parser.parse_args()

    if args.command == "prepare-function":
        prepare_function(header_file=args.header, src_file=args.source, function_name=args.function, use_klee=args.klee, main_mode=args.main_mode,
            own_main_file=args.own_main_file)
    elif args.command == "prepare-klee":
        prepare_klee(header_file=args.header, src_file=args.source, function_name=args.function)    
    elif args.command == "trace-analysis":
        trace_analysis(args.binary, args.file)
    elif args.command == "compare-runs":
        compare_json_runs(folder=args.directory, files=args.files)
    elif args.command == "func-analysis":
        binary_file = prepare_function(header_file=args.header, src_file=args.source, function_name=args.function, main_mode=args.main_mode,
                own_main_file=args.own_main_file)
        json_result = trace_analysis(binary_file)    
        
        if args.result_file:
            with open(args.result_file, "w") as f:
                f.write(json_result)

        print(json_result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

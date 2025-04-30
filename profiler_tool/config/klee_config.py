# klee_config.py

# Cesta nebo název nástroje pro čtení .ktest souborů vytvořených nástrojem KLEE.
# Pokud není 'ktest-tool' dostupný v systému, lze tuto proměnnou přesměrovat
# na alternativní nástroj nebo absolutní cestu.
KTEST_TOOL = "ktest-tool"

# Spustitelný soubor KLEE – pokud není v PATH, může se zde zadat absolutní cesta.
KLEE_EXECUTABLE = "klee"

# Definice velikosti symbolických vstupních polí pro KLEE.
# Tato konstanta se zapisuje do generovaného C souboru jako:
#     #define KLEE_SYMBOLIC_SIZE <hodnota>
# Používá se např. při symbolickém zadávání řetězců, polí a bufferů.
KLEE_SYMBOLIC_SIZE = 10

# Výchozí volby pro spouštění KLEE.
# Lze je upravit podle potřeb testování nebo prostředí.
KLEE_OPTIONS = [
    "--optimize",                           # Optimalizace IR před symbolickým spuštěním
    "--libc=uclibc",                        # Použít uClibc jako knihovnu C
    "--posix-runtime",                      # Povolit POSIX režim (umožňuje např. práci s argv, stdin)
    "--only-output-states-covering-new",    # Vypisuj jen stavy pokrývající nový kód
    "--max-time=2min",                      # Maximální doba běhu (např. pro CI nebo testování)
    "--max-memory=4096",                    # Limit paměti v MB
    "--max-forks=10000"                     # Maximální počet větví při analýze
]

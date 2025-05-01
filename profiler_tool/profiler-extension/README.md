# Profiler Extension for VS Code

Toto rozšíření pro Visual Studio Code poskytuje grafické rozhraní pro nástroj `profiler_tool`.

## Funkce
- Spouštění analýzy funkcí přes GUI
- Podpora interaktivního zadávání vstupů
- Možnost zobrazit JSON výstupy a porovnat běhy

## Požadavky
- Mít nainstalovaný `profiler_tool` v kořenové složce
- Node.js a npm

## Instalace (pro vývojáře)
```bash
cd profiler-extension
npm install
code .
```

Pak spusť VS Code v režimu rozšíření (F5) nebo pomocí „Run Extension“.

## Použití
1. Otevřete projekt obsahující `profiler_tool`.
2. Pomocí příslušného panelu v postranním menu můžete:
   - Spustit funkci s předdefinovanými vstupy
   - Zobrazit výsledek ve formátu JSON se zvýrazněním kódu, kterého se výstup týká

## Poznámky
- Zadávání parametrů analýzy se provádí standardně přes terminál stejně jako při přímém použití nástroje.
- Rozšíření slouží hlavně ke zpřehlednění a usnadnění běžných operací při práci s `profiler_tool`.

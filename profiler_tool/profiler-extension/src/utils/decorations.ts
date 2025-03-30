import * as vscode from 'vscode';

let instructionMap = new Map<string, number>(); // Globální mapa pro instrukce
let activeDecorations: vscode.TextEditorDecorationType[] = []; // Globální seznam aktivních dekorací

// Dynamické určení dekorace na základě počtu instrukcí a případného pádu
export function getDecorationType(instructionCount: number, isCrash: boolean): vscode.TextEditorDecorationType {
    if (isCrash) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 0, 0.3)',
            textDecoration: 'underline black',
        });
    } else if (instructionCount > 500) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 140, 0, 0.3)',
            textDecoration: 'underline black',
        });
    } else if (instructionCount > 100) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 255, 102, 0.3)',
            textDecoration: 'underline',
        });
    } else {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(144, 238, 144, 0.3)',
        });
    }
}
export function highlightLines(document: vscode.TextDocument, instructions: { [key: string]: number }, crashLine?: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document === document);
    if (!editor) {
        console.log("Editor not found for the document");
        return;
    }

    console.log("Removing old decorations...");
    // Odstraníme staré dekorace
    activeDecorations.forEach(decoration => decoration.dispose());
    activeDecorations = []; // Vyčistíme seznam aktivních dekorací

    console.log("Highlighting lines...");
    instructionMap.clear(); // Vyčistíme starou mapu instrukcí před novým zvýrazněním

    for (const line in instructions) {
        const match = line.match(/(.*):(\d+)$/);

        if (match) {
            const [, , lineNumber] = match;
            const lineNum = parseInt(lineNumber, 10);
            const range = document.lineAt(lineNum - 1).range;
            const isCrash = crashLine === line;
            const instructionCount = instructions[line];
            const decorationType = getDecorationType(instructionCount, isCrash);
            editor.setDecorations(decorationType, [{ range }]);


            // Uložíme dekoraci pro pozdější odstranění
            activeDecorations.push(decorationType);
            instructionMap.set(`${document.uri.toString()}:${lineNum}`, instructionCount);
        } else {
            console.log(`No MATCH!  ${line}`);
        }
    }
}

// Nastavení hover poskytovatele pro zobrazení informací o počtu instrukcí
export function setupHoverProvider(): vscode.Disposable {
    return vscode.languages.registerHoverProvider('*', {
        provideHover(document, position, token) {
            const line = position.line + 1;
            const key = `${document.uri.toString()}:${line}`;

            // Získání počtu instrukcí pro daný řádek (tuto mapu je třeba naplnit v highlightLines nebo jinde)
            if (instructionMap.has(key)) {
                const instructionCount = instructionMap.get(key);
                return new vscode.Hover(`💡 Počet instrukcí: **${instructionCount}**`);
            }

            return null; // Pokud nejsou instrukce k dispozici
        }
    });
}
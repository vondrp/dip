import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

let instructionMap = new Map<string, number>(); // Globální mapa pro instrukce
let activeDecorations: vscode.TextEditorDecorationType[] = []; // Globální seznam aktivních dekorací
let cachedConfig: any = null; // Uložená konfigurace

/**
 * Rekurzivně hledá soubor `highlightSettings.json` ve zadaném adresáři.
 * @param dir - Cesta k adresáři, ve kterém hledáme konfigurační soubor.
 * @returns Cesta k souboru, pokud je nalezen, jinak `null`.
 */
function findConfigFile(dir: string): string | null {
    try {
        const files = fs.readdirSync(dir);
        for (let file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);

            if (file === 'highlightSettings.json' && stat.isFile()) {
                return filePath;
            }

            if (stat.isDirectory()) {
                const result = findConfigFile(filePath);
                if (result) return result;
            }
        }
    } catch (error) {
        console.error("Error searching for config file:", error);
    }
    return null;
}

/**
 * Načte konfiguraci z JSON souboru, pokud již nebyla načtena.
 * @returns Vrací konfiguraci jako objekt nebo `null`, pokud došlo k chybě při načítání.
 */
function loadConfig(): any {
    if (cachedConfig) return cachedConfig; // Použijeme uloženou konfiguraci

    const rootPath = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
    if (!rootPath) {
        console.error('Workspace root path is not available.');
        return null;
    }

    const configPath = findConfigFile(rootPath);
    if (configPath) {
        try {
            console.log(`Nalezený soubor konfigurace: ${configPath}`);
            const rawConfig = fs.readFileSync(configPath, 'utf-8');
            cachedConfig = JSON.parse(rawConfig);
            return cachedConfig;
        } catch (error) {
            console.error("Error loading config file:", error);
        }
    } else {
        console.warn('Config file not found, falling back to defaults');
    }

    return null;
}

/**
 * Vytvoří dekoraci pro zvýraznění řádku na základě počtu instrukcí a případného pádu programu.
 * @param instructionCount - Počet instrukcí na daném řádku.
 * @param isCrash - Určuje, zda tento řádek odpovídá místu pádu programu.
 * @returns Dekoraci pro editor, která bude aplikována na daný řádek.
 */
export function getDecorationType(instructionCount: number, isCrash: boolean): vscode.TextEditorDecorationType {
    const config = loadConfig() || {}; // Pokud není config, použijeme prázdný objekt

    if (isCrash) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: config.crashColor || 'rgba(255, 0, 0, 0.3)',
            textDecoration: config.crashTextDecoration || 'underline wavy red',
        });
    }

    const thresholds = config.thresholds || [];
    for (let i = thresholds.length - 1; i >= 0; i--) {
        if (instructionCount > thresholds[i].limit) {
            return vscode.window.createTextEditorDecorationType({
                backgroundColor: thresholds[i].color,
                textDecoration: thresholds[i].textDecoration,
            });
        }
    }

    return vscode.window.createTextEditorDecorationType({
        backgroundColor: config.defaultLowInstructionColor || 'rgba(144, 238, 144, 0.3)',
    });
}

/**
 * Zvýrazní řádky v dokumentu na základě počtu instrukcí.
 * @param document - Dokument, ve kterém budou řádky zvýrazněny.
 * @param instructions - Mapa, která obsahuje počet instrukcí pro každý řádek.
 * @param crashLine - (Volitelné) Řádek, kde došlo k pádu programu.
 */
export function highlightLines(document: vscode.TextDocument, instructions: { [key: string]: number }, crashLine?: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document === document);
    if (!editor) return;

    activeDecorations.forEach(decoration => decoration.dispose());
    activeDecorations = [];
    instructionMap.clear();

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

            activeDecorations.push(decorationType);
            instructionMap.set(`${document.uri.toString()}:${lineNum}`, instructionCount);
        }
    }
}

/**
 * Nastaví poskytovatele hover efektů pro zobrazení počtu instrukcí na daném řádku.
 * @returns Vrací instanci `vscode.Disposable` pro správu životního cyklu poskytovatele.
 */
export function setupHoverProvider(): vscode.Disposable {
    return vscode.languages.registerHoverProvider('*', {
        provideHover(document, position) {
            const line = position.line + 1;
            const key = `${document.uri.toString()}:${line}`;
            if (instructionMap.has(key)) {
                return new vscode.Hover(`Počet instrukcí: **${instructionMap.get(key)}**`);
            }
            return null;
        }
    });
}

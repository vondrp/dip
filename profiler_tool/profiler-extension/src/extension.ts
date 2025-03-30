import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';

// Načtení JSON souboru
function loadJsonFile(filePath: string): any {
    try {
        const rawData = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(rawData);
    } catch (error) {
        if (error instanceof Error) {
            vscode.window.showErrorMessage(`Error reading JSON file: ${error.message}`);
        } else {
            vscode.window.showErrorMessage('An unknown error occurred while reading the JSON file.');
        }
        return null;
    }
}

// Dynamické určení dekorace na základě počtu instrukcí a případného pádu
function getDecorationType(instructionCount: number, isCrash: boolean): vscode.TextEditorDecorationType {
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

// Mapování instrukcí pro hover info
const instructionMap = new Map<string, number>();

// Uložené dekorace, abychom je mohli odstranit při dalším běhu
let activeDecorations: vscode.TextEditorDecorationType[] = [];

// Zvýraznění řádků v editoru
function highlightLines(document: vscode.TextDocument, instructions: { [key: string]: number }, crashLine?: string) {
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

            // Uložíme dekoraci pro pozdější odstranění
            activeDecorations.push(decorationType);

            instructionMap.set(`${document.uri.toString()}:${lineNum}`, instructionCount);
        }
        else
        {
            console.log(`No MATCH!  ${line}`)
        }
    }
}

// Aktivace rozšíření
export function activate(context: vscode.ExtensionContext) {
    console.log('Profiler Extension is now active!');
    
    const highlightCommand = vscode.commands.registerCommand('profiler-extension.highlightCode', async () => {
        const options: vscode.OpenDialogOptions = {
            canSelectMany: false,
            openLabel: 'Select JSON file',
            filters: { 'JSON Files': ['json'], 'All Files': ['*'] }
        };

        const fileUri = await vscode.window.showOpenDialog(options);
        if (!fileUri || fileUri.length === 0) {
            vscode.window.showErrorMessage('No file selected');
            return;
        }
        const jsonFilePath = fileUri[0].fsPath;
        const data = loadJsonFile(jsonFilePath);
        if (!data) return;

        vscode.workspace.openTextDocument(data.source_file).then(document => {
            vscode.window.showTextDocument(document).then(() => {
                console.log("Instructions data:", data.instructions);
                highlightLines(document, data.instructions, data.crash_last_executed_line);
            });
        });
    });
    
    const hoverProvider = vscode.languages.registerHoverProvider('*', {
            provideHover(document, position, token) {
                const key = `${document.uri.toString()}:${position.line + 1}`;
                if (instructionMap.has(key)) {
                    const instructionCount = instructionMap.get(key);
                    return new vscode.Hover(`💡 **Počet instrukcí:** ${instructionCount}`);
                }
                return null;
            }
        });
    
    const clickListener = vscode.window.onDidChangeTextEditorSelection(event => {
        const editor = event.textEditor;
        if (!editor.selection.isEmpty) return;

        const line = editor.selection.active.line + 1;
        const key = `${editor.document.uri.toString()}:${line}`;
        if (instructionMap.has(key)) {
            vscode.window.setStatusBarMessage(`💡 Řádek ${line}: **${instructionMap.get(key)} instrukcí**`, 3000);
        }
    });


    const selectFunctionCommand = vscode.commands.registerCommand('profiler.selectFunction', async () => {
        const headerFile = await selectFile('Vyber hlavičkový soubor (.h)', ['h']);
        const sourceFile = await selectFile('Vyber zdrojový soubor (.c)', ['c']);
        if (!headerFile || !sourceFile) return;
        const functionName = await vscode.window.showInputBox({ prompt: 'Zadejte název funkce' });
        if (!functionName) return;
        const useKlee = await vscode.window.showQuickPick(['Ano', 'Ne'], { placeHolder: 'Použít KLEE analýzu k získání možných vstupů?' });
    
        const kleeFlag = useKlee === 'Ano' ? '--klee' : '';
    
        runPythonScript('core.cli', `select-function -H "${headerFile}" -c "${sourceFile}" -f "${functionName}" ${kleeFlag}`);
    });

    const runTraceCommand = vscode.commands.registerCommand('profiler.runTrace', async () => {
        const binaryFile = await selectFile('Vyber binární soubor', ['out']);
        if (!binaryFile) return;
        runPythonScript('core.cli', `run-trace -b "${binaryFile}"`);
    });

    // Registrace příkazu pro porovnání běhů
    const compareRunsCommand = vscode.commands.registerCommand('profiler.compareRuns', compareRuns);

    context.subscriptions.push(highlightCommand, hoverProvider, clickListener, selectFunctionCommand, runTraceCommand, compareRunsCommand);
}

async function compareRuns() {
    const choice = await vscode.window.showQuickPick(
        ["Vybrat složku s JSON soubory", "Vybrat konkrétní JSON soubory"],
        { placeHolder: "Jak chcete porovnat běhy?" }
    );

    if (!choice) return;

    let commandArgs = "";

    if (choice === "Vybrat složku s JSON soubory") {
        const folderUri = await vscode.window.showOpenDialog({
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: "Vyber složku s JSON soubory"
        });

        if (!folderUri || folderUri.length === 0) {
            vscode.window.showErrorMessage("❌ Nebyla vybrána žádná složka.");
            return;
        }

        commandArgs = `compare-runs -d "${folderUri[0].fsPath}"`;

    } else if (choice === "Vybrat konkrétní JSON soubory") {
        const fileUris = await vscode.window.showOpenDialog({
            canSelectMany: true,
            openLabel: "Vyber JSON soubory",
            filters: { "JSON Files": ["json"] }
        });

        if (!fileUris || fileUris.length === 0) {
            vscode.window.showErrorMessage("❌ Nebyly vybrány žádné soubory.");
            return;
        }

        const filePaths = fileUris.map(uri => `"${uri.fsPath}"`).join(" ");
        commandArgs = `compare-runs -f ${filePaths}`;
    }

    runPythonScript('core.cli', commandArgs);
}


async function selectFile(title: string, filters: string[]): Promise<string | undefined> {
    const options: vscode.OpenDialogOptions = { canSelectMany: false, openLabel: title, filters: { 'Soubory': filters } };
    const result = await vscode.window.showOpenDialog(options);
    return result?.[0]?.fsPath;
}

async function runPythonScript(module: string, args: string) {
    const pythonPath = 'python3'; // nebo 'python', pokud používáš jinou verzi
    const shell = process.env.SHELL || 'sh'; // Pokud /bin/sh není, použije se shell z prostředí
    const modulePath = path.join(__dirname, 'core');  // Určení cesty k modulu
    const command = `${pythonPath} -m core.cli ${args}`;
    
    // Vytvoření terminálu
    const terminal = vscode.window.createTerminal({
        name: 'Profiler Python Script',
        cwd: path.join(__dirname, '..', '..')  // Pracovní adresář pro terminál
    });

    // Poslání příkazu do terminálu
    terminal.sendText(command);
    terminal.show();  // Zobrazíme terminál pro uživatele

    // Můžeme také zobrazit nějakou zprávu, pokud to potřebujeme pro informaci uživatele
    vscode.window.showInformationMessage(`Spouštím skript: ${command}`);
}



export function deactivate() {}

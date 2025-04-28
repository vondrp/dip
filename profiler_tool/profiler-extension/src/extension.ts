import * as vscode from 'vscode';
import { ProfilerSidebarProvider } from './sidebarProvider';
import { highlightLines, setupHoverProvider } from './utils/decorations';
import { selectFile, loadJsonFile } from './utils/fileUtils';
import { runPythonScript, runPythonScriptReturn } from './utils/pythonRunner';

/**
 * Aktivuje rozšíření Profiler, registruje příkazy a poskytuje Sidebar.
 * Tento kód inicializuje všechny příkazy a služby, které jsou k dispozici
 * po aktivaci rozšíření v prostředí Visual Studio Code.
 * 
 * @param context - Kontext rozšíření, který obsahuje informace o stavu rozšíření a správu životního cyklu.
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('Profiler Extension is now active!');
    
    // Registrace Sidebaru do VS Code
    const sidebarProvider = new ProfilerSidebarProvider(context);
    console.log("Registering sidebar provider");
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ProfilerSidebarProvider.viewType, sidebarProvider)
    );

    // Registrace příkazů, které jsou dostupné pro uživatele v příkazové paletě
    context.subscriptions.push(
        vscode.commands.registerCommand('profiler-extension.highlightCode', async () => {
            // Příkaz pro zvýraznění kódu na základě souboru JSON s instrukcemi
            const fileUri = await vscode.window.showOpenDialog({
                canSelectMany: false,
                openLabel: 'Select JSON file',
                filters: { 'JSON Files': ['json'], 'All Files': ['*'] }
            });
            if (!fileUri || fileUri.length === 0) return;
            
            const jsonFilePath = fileUri[0].fsPath;
            const data = loadJsonFile(jsonFilePath);
            if (!data) return;
            
            // Otevření souboru a aplikování zvýraznění na základě dat z JSON
            vscode.workspace.openTextDocument(data.source_file).then(document => {
                vscode.window.showTextDocument(document).then(() => {
                    highlightLines(document, data.instructions, data.crash_last_executed_line);
                });
            });
        }),
        
        vscode.commands.registerCommand('profiler.prepareFunction', async () => {
            // Příkaz pro přípravu funkce pro analýzu
            const headerFile = await selectFile('Vyber hlavičkový soubor (.h)', ['h']);
            const sourceFile = await selectFile('Vyber zdrojový soubor (.c)', ['c']);
            if (!headerFile || !sourceFile) return;
            
            const functionName = await vscode.window.showInputBox({ prompt: 'Zadejte název funkce' });
            if (!functionName) return;
            
            const useKlee = await vscode.window.showQuickPick(['Ano', 'Ne'], { placeHolder: 'Použít KLEE analýzu?' });
            const kleeFlag = useKlee === 'Ano' ? '--klee' : '';

            const mainMode = await vscode.window.showQuickPick(['auto', 'template', 'own'], { placeHolder: 'Vyberte mód generování main.c' });
            if (!mainMode) return;

            let ownMainFileArg = '';
            if (mainMode === 'own') {
                const ownMainFile = await selectFile('Vyberte vlastní main soubor (.c)', ['c']);
                if (!ownMainFile) {
                    vscode.window.showErrorMessage('Musíte vybrat vlastní main soubor pro mód "own".');
                    return;
                }
                ownMainFileArg = `--own-main-file "${ownMainFile}"`;
            }

            // Spuštění Python skriptu pro přípravu funkce
            const command = `prepare-function -H "${headerFile}" -c "${sourceFile}" -f "${functionName}" --main-mode ${mainMode} ${ownMainFileArg} ${kleeFlag}`;
            runPythonScript('core.cli', command.trim());
        }),

        vscode.commands.registerCommand('profiler.traceAnalysis', async () => {
            // Příkaz pro analýzu trace souboru (binární soubor)
            const binaryFile = await selectFile('Vyber binární soubor', ['out']);
            if (!binaryFile) return;
            runPythonScript('core.cli', `trace-analysis -b "${binaryFile}"`);
        }),

        vscode.commands.registerCommand('profiler.compareRuns', async () => {
            // Příkaz pro porovnání výsledků více běhů
            const folderUri = await vscode.window.showOpenDialog({
                canSelectFolders: true,
                canSelectMany: false,
                openLabel: 'Vyber složku s JSON soubory'
            });
            if (!folderUri || folderUri.length === 0) return;
            runPythonScript('core.cli', `compare-runs -d "${folderUri[0].fsPath}"`);
        }),

        vscode.commands.registerCommand('profiler.kleeAnalysis', async () => {
            // Příkaz pro provedení analýzy pomocí nástroje KLEE
            const headerFile = await selectFile('Vyber hlavičkový soubor (.h)', ['h']);
            const sourceFile = await selectFile('Vyber zdrojový soubor (.c)', ['c']);
            if (!headerFile || !sourceFile) return;
            
            const functionName = await vscode.window.showInputBox({ prompt: 'Zadejte název funkce (nepovinné)' });
            if (!functionName) {
                console.log("Funkce není zadána, pokračujeme bez funkce");
                runPythonScript('core.cli', `prepare-klee -H "${headerFile}" -c "${sourceFile}"`);
            } else {
                runPythonScript('core.cli', `prepare-klee -H "${headerFile}" -c "${sourceFile}" -f "${functionName}"`);
            }            
        }),

        vscode.commands.registerCommand('profiler.functionAnalysis', async () => {
            // Příkaz pro analýzu funkce
            const headerFile = await selectFile('Vyber hlavičkový soubor (.h)', ['h']);
            const sourceFile = await selectFile('Vyber zdrojový soubor (.c)', ['c']);
            if (!headerFile || !sourceFile) return;
            
            const functionName = await vscode.window.showInputBox({ prompt: 'Zadejte název funkce (nepovinné)' });

            const mainMode = await vscode.window.showQuickPick(['auto', 'template', 'own'], { placeHolder: 'Vyberte mód generování main.c' });
            if (!mainMode) return;

            let ownMainFileArg = '';
            if (mainMode === 'own') {
                const ownMainFile = await selectFile('Vyberte vlastní main soubor (.c)', ['c']);
                if (!ownMainFile) {
                    vscode.window.showErrorMessage('Musíte vybrat vlastní main soubor pro mód "own".');
                    return;
                }
                ownMainFileArg = `--own-main-file "${ownMainFile}"`;
            }

            // Připravíme příkaz
            const command = `func-analysis -H "${headerFile}" -c "${sourceFile}" -f "${functionName || ''}" --main-mode ${mainMode} ${ownMainFileArg}`;

            // Spuštění Python skriptu
            const resultPath = await runPythonScriptReturn('core.cli.main', command.trim());
            if (!resultPath) {
                vscode.window.showErrorMessage('Chyba: nebyla vrácena cesta k výsledku analýzy.');
                return;
            }

            const data = loadJsonFile(resultPath);
            if (!data) return;
            
            // Otevření souboru a aplikování zvýraznění na základě výsledků analýzy
            vscode.workspace.openTextDocument(data.source_file).then(document => {
                vscode.window.showTextDocument(document).then(() => {
                    highlightLines(document, data.instructions, data.crash_last_executed_line);
                });
            });
        })
    );
    
    // Registrace hover provideru pro zobrazení počtu instrukcí při najetí myší
    context.subscriptions.push(setupHoverProvider());
}

/**
 * Deaktivuje rozšíření Profiler.
 * Tento kód bude spuštěn při deaktivaci rozšíření.
 */
export function deactivate() {}

import * as vscode from 'vscode';
import { ProfilerSidebarProvider } from './sidebarProvider';
import { highlightLines, setupHoverProvider } from './utils/decorations';
import { selectFile, loadJsonFile } from './utils/fileUtils';
import { runPythonScript } from './utils/pythonRunner';

export function activate(context: vscode.ExtensionContext) {
    console.log('Profiler Extension is now active!');
    
    // Registrace Sidebaru
    const sidebarProvider = new ProfilerSidebarProvider(context);
    console.log("Registering sidebar provider");
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ProfilerSidebarProvider.viewType, sidebarProvider)
    );

    
    // Příkazy
    context.subscriptions.push(
        vscode.commands.registerCommand('profiler-extension.highlightCode', async () => {
            const fileUri = await vscode.window.showOpenDialog({
                canSelectMany: false,
                openLabel: 'Select JSON file',
                filters: { 'JSON Files': ['json'], 'All Files': ['*'] }
            });
            if (!fileUri || fileUri.length === 0) return;
            
            const jsonFilePath = fileUri[0].fsPath;
            const data = loadJsonFile(jsonFilePath);
            if (!data) return;
            
            vscode.workspace.openTextDocument(data.source_file).then(document => {
                vscode.window.showTextDocument(document).then(() => {
                    highlightLines(document, data.instructions, data.crash_last_executed_line);
                });
            });
        }),
        
        vscode.commands.registerCommand('profiler.prepareFunction', async () => {
            const headerFile = await selectFile('Vyber hlavičkový soubor (.h)', ['h']);
            const sourceFile = await selectFile('Vyber zdrojový soubor (.c)', ['c']);
            if (!headerFile || !sourceFile) return;
            
            const functionName = await vscode.window.showInputBox({ prompt: 'Zadejte název funkce' });
            if (!functionName) return;
            
            const useKlee = await vscode.window.showQuickPick(['Ano', 'Ne'], { placeHolder: 'Použít KLEE analýzu?' });
            const kleeFlag = useKlee === 'Ano' ? '--klee' : '';
            runPythonScript('core.cli', `prepare-function -H "${headerFile}" -c "${sourceFile}" -f "${functionName}" ${kleeFlag}`);
        }),

        vscode.commands.registerCommand('profiler.traceAnalysis', async () => {
            const binaryFile = await selectFile('Vyber binární soubor', ['out']);
            if (!binaryFile) return;
            runPythonScript('core.cli', `trace-analysis -b "${binaryFile}"`);
        }),

        vscode.commands.registerCommand('profiler.compareRuns', async () => {
            const folderUri = await vscode.window.showOpenDialog({
                canSelectFolders: true,
                canSelectMany: false,
                openLabel: 'Vyber složku s JSON soubory'
            });
            if (!folderUri || folderUri.length === 0) return;
            runPythonScript('core.cli', `compare-runs -d "${folderUri[0].fsPath}"`);
        })
    );
    
    // Hover info
    context.subscriptions.push(setupHoverProvider());
}

export function deactivate() {}

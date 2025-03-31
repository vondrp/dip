import * as vscode from 'vscode';
import * as path from 'path';

export async function runPythonScript(module: string, args: string) {
    const pythonPath = 'python3';
    const shell = process.env.SHELL || 'sh';
    const modulePath = path.join(__dirname, 'core');
    const command = `${pythonPath} -m core.cli.main ${args}`;
    
    // Logování pro kontrolu cesty k modulu
    console.log('Cesta k modulu:', modulePath);

    console.log('Spouštěný příkaz:', command);

    // Vytvoření terminálu
    const terminal = vscode.window.createTerminal({
        name: 'Profiler Python Script',
        cwd: path.join(__dirname, '..', '..', '..')  // Pracovní adresář pro terminál
    });

    // Logování pracovní cesty pro terminál
    console.log('Cesta pro pracovní adresář terminálu:', path.join(__dirname, '..', '..', '..'));

    // Poslání příkazu do terminálu
    terminal.sendText(command);
    terminal.show();  // Zobrazíme terminál pro uživatele

    // Můžeme také zobrazit nějakou zprávu, pokud to potřebujeme pro informaci uživatele
    vscode.window.showInformationMessage(`Spouštím skript: ${command}`);
}

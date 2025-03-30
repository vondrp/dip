import * as vscode from 'vscode';
import * as path from 'path';

export async function runPythonScript(module: string, args: string) {
    const pythonPath = 'python3'; // nebo 'python', pokud používáš jinou verzi
    const shell = process.env.SHELL || 'sh'; // Pokud /bin/sh není, použije se shell z prostředí
    const modulePath = path.join(__dirname, 'core');  // Určení cesty k modulu
    const command = `${pythonPath} -m core.cli ${args}`;
    
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

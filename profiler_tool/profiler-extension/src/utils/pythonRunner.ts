import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import * as crypto from 'crypto';

/**
 * Vygeneruje dočasný soubor pro uchování výsledků.
 * @returns Cesta k vygenerovanému dočasnému souboru.
 */
function generateTempFile(): string {
    const random = crypto.randomBytes(8).toString('hex');
    return path.join(os.tmpdir(), `profiler-result-${random}.txt`);
}

/**
 * Spustí Python skript a vrátí výstup do souboru.
 * @param module - Název modulu, který se má spustit.
 * @param args - Argumenty pro spuštění modulu.
 * @returns Vrátí obsah výsledného souboru po jeho vytvoření a zápisu.
 */
export async function runPythonScriptReturn(module: string, args: string): Promise<string> {
    const tempFile = generateTempFile();
    const fullCommand = `python3 -m ${module} ${args} --result-file "${tempFile}"`;

    const terminal = vscode.window.createTerminal({
        name: 'Profiler Python Script',
        cwd: path.join(__dirname, '..', '..', '..')
    });

    terminal.sendText(fullCommand);
    terminal.show();

    vscode.window.showInformationMessage(`Spouštím skript: ${fullCommand}`);

    return await watchForFileChange(tempFile);
}

/**
 * Čeká na zápis do souboru pomocí `fs.watchFile` a vrací obsah souboru.
 * @param filePath - Cesta k souboru, který bude sledován.
 * @returns Vrátí obsah souboru, jakmile bude zapsán.
 */
function watchForFileChange(filePath: string): Promise<string> {
    return new Promise((resolve, reject) => {
        const checkAndResolve = () => {
            fs.readFile(filePath, 'utf8', (err, data) => {
                if (!err && data.trim().length > 0) {
                    fs.unwatchFile(filePath);  // Odpoj watcher
                    resolve(data.trim());
                }
            });
        };

        fs.watchFile(filePath, { interval: 1000 }, () => {
            checkAndResolve();
        });
    });
}

/**
 * Spustí Python skript v terminálu bez čekání na výstup.
 * @param module - Název modulu, který se má spustit.
 * @param args - Argumenty pro spuštění modulu.
 */
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

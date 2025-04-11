import * as vscode from 'vscode';
import * as fs from 'fs';

/**
 * Načte obsah JSON souboru.
 * @param filePath - Cesta k souboru, který má být načten.
 * @returns Vrací obsah souboru jako objekt, pokud byl soubor úspěšně načten a převeden na JSON, nebo `null` v případě chyby.
 */
export function loadJsonFile(filePath: string): any {
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

/**
 * Otevře dialog pro výběr souboru.
 * @param title - Titulek okna pro výběr souboru.
 * @param filters - Filtry pro výběr souborů (například přípony souborů).
 * @returns Vrací cestu k vybranému souboru nebo `undefined`, pokud uživatel nevybral žádný soubor.
 */
export async function selectFile(title: string, filters: string[]): Promise<string | undefined> {
    const options: vscode.OpenDialogOptions = { canSelectMany: false, openLabel: title, filters: { 'Soubory': filters } };
    const result = await vscode.window.showOpenDialog(options);
    return result?.[0]?.fsPath;
}

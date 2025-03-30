import * as vscode from 'vscode';
import * as fs from 'fs';

// Načtení JSON souboru
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

// Funkce pro výběr souboru z dialogu
export async function selectFile(title: string, filters: string[]): Promise<string | undefined> {
    const options: vscode.OpenDialogOptions = { canSelectMany: false, openLabel: title, filters: { 'Soubory': filters } };
    const result = await vscode.window.showOpenDialog(options);
    return result?.[0]?.fsPath;
}

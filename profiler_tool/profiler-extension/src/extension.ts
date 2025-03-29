import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

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
            backgroundColor: 'rgba(255, 0, 0, 0.5)', // Červená pro pád
            border: '2px solid black',
        });
    } else if (instructionCount > 500) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 102, 0, 0.5)', // Oranžová pro hodně instrukcí
        });
    } else if (instructionCount > 100) {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 255, 0, 0.5)', // Žlutá pro střední počet instrukcí
        });
    } else {
        return vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(153, 255, 153, 0.5)', // Zelená pro málo instrukcí
        });
    }
}


// Zvýraznění řádků v editoru
function highlightLines(document: vscode.TextDocument, instructions: { [key: string]: number }, crashLine?: string) {
	console.log('Executing highlightCode command...');
    const editor = vscode.window.visibleTextEditors.find(e => e.document === document);
    if (!editor) {
		console.log('Executing highlightCode command EDITOR not found');
		return;
	}

	console.log('Executing highlightCode command BEFORE FOR cycle');


    for (const line in instructions) {
        const match = line.match(/(.*):(\d+)$/);
        if (match) {
            const [, , lineNumber] = match;
            const lineNum = parseInt(lineNumber, 10);
            const range = document.lineAt(lineNum - 1).range;
            const isCrash = crashLine === line;
            const decorationType = getDecorationType(instructions[line], isCrash);
            editor.setDecorations(decorationType, [{ range }]);
        }
    }
}

// Aktivace rozšíření
export function activate(context: vscode.ExtensionContext) {
    console.log('Profiler Extension is now active!');

	const disposable = vscode.commands.registerCommand('profiler-extension.highlightCode', async () => {
        const options: vscode.OpenDialogOptions = {
            canSelectMany: false,
            openLabel: 'Select JSON file',
            filters: {
                'JSON Files': ['json'],
                'All Files': ['*']
            }
        };

        const fileUri = await vscode.window.showOpenDialog(options);
        if (!fileUri || fileUri.length === 0) {
            vscode.window.showErrorMessage('No file selected');
            return;
        }

        const jsonFilePath = fileUri[0].fsPath;
        const data = loadJsonFile(jsonFilePath);
        if (!data) {
			return;
		}	

        vscode.workspace.openTextDocument(data.source_file).then(document => {
            vscode.window.showTextDocument(document).then(() => {
                highlightLines(document, data.instructions, data.crash_last_executed_line);
            });
        });
    });



	/** 
    const disposable = vscode.commands.registerCommand('profiler-extension.highlightCode', () => {
        vscode.window.showInformationMessage('Profiler Control started!');
        const jsonFilePath = '/path/to/your/json/file.json'; // Upravte podle potřeby
        const data = loadJsonFile(jsonFilePath);
        if (data) {
            highlightLines(data.source_file, data.instructions, data.crash_last_executed_line);
        }
        vscode.window.showInformationMessage('Profiler Control END!');
    });
	*/
    context.subscriptions.push(disposable);
}

// Deaktivace rozšíření
export function deactivate() {}

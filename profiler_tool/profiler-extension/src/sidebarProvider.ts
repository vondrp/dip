import * as vscode from "vscode";

/**
 * Tato třída poskytuje Sidebar pro rozšíření Profiler v aplikaci Visual Studio Code.
 * Sidebar obsahuje tlačítka pro různé akce, které uživatel může spustit, jako je analýza funkce, příprava funkce a další.
 */
export class ProfilerSidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = "profilerSidebar"; // Typ view, který je používán pro identifikaci tohoto webview.

    constructor(private readonly context: vscode.ExtensionContext) {}

    /**
     * Funkce pro zajištění správného zobrazení a interakce s webview.
     * Tato metoda je volána, když je webview inicializováno.
     *
     * @param webviewView - Webview, který je propojen s tímto poskytovatelem.
     */
    resolveWebviewView(webviewView: vscode.WebviewView) {
        console.log("Resolving webview view...");

        // Nastavení možností webview - povolujeme skripty, aby webview mohl vykonávat JavaScript.
        webviewView.webview.options = { enableScripts: true };

        // Nastavení HTML obsahu pro webview
        webviewView.webview.html = this.getHtml(webviewView);

        // Poslouchání zpráv přicházejících z webview a provádění příslušných příkazů na základě příkazu zprávy
        webviewView.webview.onDidReceiveMessage((message) => {
            console.log("Received message from webview:", message);
            switch (message.command) {
                case 'profiler-extension.highlightCode':
                    // Spustí příkaz pro zvýraznění kódu
                    vscode.commands.executeCommand('profiler-extension.highlightCode');
                    return;
                case 'profiler.prepareFunction':
                    // Spustí příkaz pro přípravu funkce pro analýzu
                    vscode.commands.executeCommand('profiler.prepareFunction');
                    return;
                case 'profiler.traceAnalysis':
                    // Spustí příkaz pro analýzu trace souboru
                    vscode.commands.executeCommand('profiler.traceAnalysis');
                    return;
                case 'profiler.compareRuns':
                    // Spustí příkaz pro porovnání běhů
                    vscode.commands.executeCommand('profiler.compareRuns');
                    return;
                case 'profiler.kleeAnalysis':
                    // Spustí příkaz pro provedení analýzy pomocí KLEE
                    vscode.commands.executeCommand('profiler.kleeAnalysis');
                    return;    
                case 'profiler.functionAnalysis':
                    // Spustí příkaz pro analýzu funkce
                    vscode.commands.executeCommand('profiler.functionAnalysis');
                    return;    
            }
        });
    }

    /**
     * Vrací HTML obsah pro webview, který definuje vzhled a strukturu sidebaru.
     * Tento HTML obsahuje tlačítka pro různé akce, které mohou uživatelé spustit.
     * 
     * @param webviewView - Webview, pro který se HTML generuje.
     * @returns HTML kód jako řetězec.
     */
    getHtml(webviewView: vscode.WebviewView): string {
        return `
            <html>
                <head>
                    <style>
                        /* Stylování pro webview */
                        body {
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 10px;
                            background-color: var(--vscode-editor-background); /* Používáme barvy podle nastavení VS Code */
                            color: var(--vscode-editor-foreground);
                        }
    
                        h2 {
                            color: var(--vscode-editor-foreground);
                        }
    
                        button {
                            background-color: var(--vscode-button-background);
                            color: var(--vscode-button-foreground);
                            padding: 10px 20px;
                            margin: 5px;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                            transition: background-color 0.2s;
                        }
    
                        button:hover {
                            background-color: var(--vscode-button-hoverBackground);
                        }
    
                        button:focus {
                            outline: 2px solid var(--vscode-focusBorder);
                        }
    
                        .container {
                            display: flex;
                            flex-direction: column;
                        }
                    </style>
                </head>
                <body>
                    <h2>Profiler Actions</h2>
                    <div class="container">
                        <!-- Tlačítka pro různé akce, která spustí příslušné příkazy -->
                        <button onclick="vscode.postMessage({ command: 'profiler.functionAnalysis' })">Function Analysis</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.prepareFunction' })">Prepare Function binary</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.traceAnalysis' })">Analyse binary</button>
                        <button onclick="vscode.postMessage({ command: 'profiler-extension.highlightCode' })">Highlight Code</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.kleeAnalysis' })">KLEE Analysis</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.compareRuns' })">Compare Runs</button>
                    </div>
                    <script>
                        // Zajištění komunikace mezi webview a VS Code prostředím
                        const vscode = acquireVsCodeApi();
                    </script>
                </body>
            </html>
        `;
    }
}

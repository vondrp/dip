import * as vscode from "vscode";

export class ProfilerSidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = "profilerSidebar";

    constructor(private readonly context: vscode.ExtensionContext) {}

    resolveWebviewView(webviewView: vscode.WebviewView) {
        console.log("Resolving webview view...");

        // Nastavení možností webview
        webviewView.webview.options = { enableScripts: true };

        // Nastavení HTML pro webview
        webviewView.webview.html = this.getHtml(webviewView);

        // Poslouchání zpráv od webview
        webviewView.webview.onDidReceiveMessage((message) => {
            console.log("Received message from webview:", message);
            switch (message.command) {
                case 'profiler-extension.highlightCode':
                    vscode.commands.executeCommand('profiler-extension.highlightCode');
                    return;
                case 'profiler.prepareFunction':
                    vscode.commands.executeCommand('profiler.prepareFunction');
                    return;
                case 'profiler.traceAnalysis':
                    vscode.commands.executeCommand('profiler.traceAnalysis');
                    return;
                case 'profiler.compareRuns':
                    vscode.commands.executeCommand('profiler.compareRuns');
                    return;
            }
        });
    }

    getHtml(webviewView: vscode.WebviewView): string {
        return `
            <html>
                <head>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 10px;
                            background-color: var(--vscode-editor-background);
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
                        <button onclick="vscode.postMessage({ command: 'profiler.prepareFunction' })">Prepare Function</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.traceAnalysis' })">Trace Analysis</button>
                        <button onclick="vscode.postMessage({ command: 'profiler-extension.highlightCode' })">Highlight Code</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.compareRuns' })">Compare Runs</button>
                    </div>
                    <script>
                        const vscode = acquireVsCodeApi();
                    </script>
                </body>
            </html>
        `;
    }
}

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
                case 'profiler.selectFunction':
                    vscode.commands.executeCommand('profiler.selectFunction');
                    return;
                case 'profiler.runTrace':
                    vscode.commands.executeCommand('profiler.runTrace');
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
                            background-color: #f4f4f4;
                        }

                        h2 {
                            color: #333;
                        }

                        button {
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            margin: 5px;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                        }

                        button:hover {
                            background-color: #45a049;
                        }

                        button:focus {
                            outline: none;
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
                        <button onclick="vscode.postMessage({ command: 'profiler-extension.highlightCode' })">Highlight Code</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.selectFunction' })">Select Function</button>
                        <button onclick="vscode.postMessage({ command: 'profiler.runTrace' })">Run Trace</button>
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

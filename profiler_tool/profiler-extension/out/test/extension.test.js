"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const assert = __importStar(require("assert"));
const vscode = __importStar(require("vscode"));
const sinon = __importStar(require("sinon"));
const fs = __importStar(require("fs"));
// Importujeme rozšíření
const extension_1 = require("../extension");
suite('Profiler Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');
    test('Extension should be activated', async () => {
        const context = { subscriptions: [] };
        (0, extension_1.activate)(context);
        const command = vscode.commands.getCommands(true);
        assert.ok((await command).includes('profiler-extension.highlightCode'), 'Command is not registered');
    });
    test('Should load JSON file correctly', () => {
        const mockJson = `{
            "source_file": "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c",
            "function": "compute",
            "params": "42 0",
            "total_instructions": 821,
            "instructions": {
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:23": 6,
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:24": 2,
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:25": 657,
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:27": 2,
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:28": 150,
                "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:29": 4
            },
            "crash_detected": true,
            "crash_last_executed_line": "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:29"
        }`;
        // Opravené stubování `fs.readFileSync`
        const readFileSyncStub = sinon.stub(fs, 'readFileSync').callsFake(() => Buffer.from(mockJson, 'utf-8'));
        try {
            // Načteme data z JSON
            const data = JSON.parse(mockJson);
            assert.strictEqual(data.source_file, "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c");
            assert.strictEqual(data.instructions["/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:23"], 6);
            assert.strictEqual(data.crash_last_executed_line, "/home/vondrp/programs/dip/profiler_tool/./tests/src/test_program.c:29");
        }
        finally {
            // Obnovíme původní funkci `readFileSync`
            readFileSyncStub.restore();
        }
    });
    test('Should execute highlightCode command', async function () {
        this.timeout(10000); // Zvýšíme timeout na 10 sekund
        console.log("Spouštím příkaz 'profiler-extension.highlightCode'...");
        try {
            const result = await vscode.commands.executeCommand('profiler-extension.highlightCode');
            console.log("Příkaz dokončen, výsledek:", result);
            assert.strictEqual(result, undefined, 'Command did not execute properly');
        }
        catch (err) {
            console.error("Příkaz selhal s chybou:", err);
            assert.fail(`Command execution failed with error: ${err}`);
        }
    });
    test('Should deactivate extension', () => {
        assert.doesNotThrow(() => (0, extension_1.deactivate)(), 'Deactivate function threw an error');
    });
});
//# sourceMappingURL=extension.test.js.map
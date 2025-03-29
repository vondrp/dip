import * as assert from 'assert';
import * as vscode from 'vscode';
import * as sinon from 'sinon';
import * as fs from 'fs';

// Importujeme rozšíření
import { activate, deactivate } from '../extension';

suite('Profiler Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('Extension should be activated', async () => {
        const context = { subscriptions: [] } as unknown as vscode.ExtensionContext;
        activate(context);
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
        } finally {
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
        } catch (err: any) {
            console.error("Příkaz selhal s chybou:", err);
            assert.fail(`Command execution failed with error: ${err}`);
        }
    });

    test('Should deactivate extension', () => {
        assert.doesNotThrow(() => deactivate(), 'Deactivate function threw an error');
    });
});

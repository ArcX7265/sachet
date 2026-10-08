import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const isWindows = process.platform === 'win32';
export const venvPython = resolve(root, isWindows ? '.venv/Scripts/python.exe' : '.venv/bin/python');
export const python = process.env.SACHET_PYTHON || (existsSync(venvPython) ? venvPython : isWindows ? 'python' : 'python3');

export function readEnv() {
  const file = resolve(root, '.env');
  if (!existsSync(file)) return;
  for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (!match || process.env[match[1]] !== undefined) continue;
    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    process.env[match[1]] = value;
  }
}

export function run(command, args, options = {}) {
  return new Promise((resolveRun, reject) => {
    const child = spawn(command, args, { cwd: root, stdio: 'inherit', windowsHide: true, ...options });
    child.once('error', reject);
    child.once('exit', code => code === 0 ? resolveRun() : reject(new Error(`${command} exited with status ${code}`)));
  });
}

// Invoke npm's JavaScript entrypoint directly, avoiding command-shell quoting.
export const npmCli = process.env.npm_execpath;
export async function npm(args, options) {
  if (npmCli) return run(process.execPath, [npmCli, ...args], options);
  throw new Error('Run this script through npm (for example: npm run setup).');
}

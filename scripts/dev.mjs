import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { root, python, readEnv } from './common.mjs';

readEnv();
const vite = resolve(root, 'apps/web/node_modules/vite/bin/vite.js');
if (!existsSync(vite)) {
  console.error('Dependencies are missing. Run npm run setup first.');
  process.exit(1);
}
mkdirSync(resolve(root, 'data'), { recursive: true });
const env = {
  ...process.env,
  PYTHONUNBUFFERED: '1',
  DEMO_MODE: process.env.DEMO_MODE || 'true',
  SACHET_DB_PATH: process.env.SACHET_DB_PATH || resolve(root, 'data/sachet.sqlite3'),
};
const children = [];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill('SIGTERM');
  process.exitCode = code;
}
function start(command, args, cwd) {
  const child = spawn(command, args, { cwd, env, stdio: 'inherit', windowsHide: true });
  children.push(child);
  child.once('error', error => { console.error(error.message); stop(1); });
  child.once('exit', code => { if (!stopping) stop(code || 0); });
  return child;
}
start(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], resolve(root, 'services/api'));
start(process.execPath, [vite, '--host', '127.0.0.1', '--port', '5173', '--strictPort'], resolve(root, 'apps/web'));
console.log('\nSachet: http://127.0.0.1:5173\nAPI: http://127.0.0.1:8000/docs\nLocal demo workspace. Keep both services bound to loopback.\n');
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());

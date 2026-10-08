import { existsSync } from 'node:fs';
import { root, python, venvPython, run, npm } from './common.mjs';

try {
  if (!existsSync(venvPython)) await run(python, ['-m', 'venv', '.venv']);
  await run(venvPython, ['-m', 'pip', 'install', '-r', 'services/api/requirements.txt']);
  await npm(['--prefix', 'apps/web', 'ci']);
  console.log(`\nSachet is ready in ${root}. Run npm run dev.`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}

import { python, root, run } from './common.mjs';
import { resolve } from 'node:path';

try {
  if (process.argv.includes('--evaluate')) {
    await run(python, ['evaluation/run.py']);
  } else {
    await run(python, ['-m', 'pytest', 'tests', '-q'], { env: { ...process.env, PYTHONPATH: resolve(root, 'services/api') } });
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}

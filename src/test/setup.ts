import { config } from 'dotenv';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

// Load .env file from project root
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..', '..');

config({ path: join(projectRoot, '.env') });

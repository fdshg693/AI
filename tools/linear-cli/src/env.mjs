import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(SCRIPT_DIRECTORY, "..");
const DEFAULT_ENV_PATH = path.join(PACKAGE_ROOT, ".env");

/** tools/linear-cli/.env を読み込む。実行時のカレントディレクトリに依存しない。 */
export function loadLocalEnv(envPath = DEFAULT_ENV_PATH) {
  try {
    process.loadEnvFile(envPath);
  } catch {
    // .env が無くても LINEAR_API_KEY が環境変数で設定済みなら問題ない。
  }
}

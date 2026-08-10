import process from "node:process";
import { LinearClient } from "@linear/sdk";

export function createClient() {
  const apiKey = process.env.LINEAR_API_KEY;
  if (!apiKey) {
    throw new Error(
      "LINEAR_API_KEY が設定されていません。環境変数、または tools/linear-cli/.env に設定してください。",
    );
  }
  return new LinearClient({ apiKey });
}

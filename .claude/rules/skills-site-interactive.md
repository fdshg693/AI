---
paths:
  - "skills-site/src/components/react/**"
  - "skills-site/api/**"
  - "skills-site/astro.config.mjs"
---

## skills-site インタラクティブUI・サーバーAPI規約

- インタラクティブ UI は React island（`src/components/react/`）で実装し、バニラJS を `public/` に増やさない。
- コンテンツページは Astro 静的生成のまま（`output: "static"`）。サーバー処理は `skills-site/api/` の SWA managed Functions（`/api/*`）のみ。Astro `src/pages/api` や hybrid/SSR adapter は使わない。
- 外部 APIキー（OpenRouter 等）はサーバー環境変数（`OPENROUTER_API_KEY`）のみで保持し、クライアントへ公開・BYOK させない。
- 検索インデックスはビルド時生成（`catalog:build` と同タイミング、`scripts/build-search-index.mjs`）し、実行時生成しない。ライブラリは MiniSearch。成果物は `api/data/` に置き Functions が `loadJSON` する。
- AI 提案用のスリム索引（`api/data/ai-index.json`）も同様にビルド時生成し、クライアントへ配信しない。

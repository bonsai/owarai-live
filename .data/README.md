# .data

お笑いライブの統合データ層。

- `events.json`: 公開検索用の主要イベントDB
- `events-*.jsonl`: ソース別・期間別に収集したイベント観測DB
- `assets.json`: Provider / Venue / Event / Organizer 等のAsset DB
- `venue.jsonl`: Venue seed / observed venue DB
- `comedians.jsonl`: 芸人・出演者Asset DB
- `agent-memory.jsonl`: 検索Agentの記憶
- `search-policy.json`: 検索・公開ポリシー

旧 `data/` は廃止し、すべて `.data/` に統合する。

## 正規化契約
- `.data/schema.json`: Asset 共通契約
- `.data/assets.json`: Provider / Venue Complex / Venue / Event / Organizer 等の正規化Asset
- `.data/events.json`: 公開表示用のEvent配列（JSON文字列ラッパーなし）
- `domes.json` / `halls.json` は廃止し、Venue Complex / Venue Assetとして `assets.json` に統合。

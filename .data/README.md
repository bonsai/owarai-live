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

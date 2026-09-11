# live-date MCP

ライブイベントをデートの「主役」にして、前後の食事・散歩・カフェ時間を組み立てる MCP サーバー。

## Tools

- `search_live_events` — 日付・エリア・ジャンル・価格・時間帯からライブを検索
- `plan_date_with_live` — ライブをアンカーに、前後のデート枠を自動生成
- `list_event_sources` — 使用中の公開データソースを表示

## Data

現在は以下の公開 JSON を読み込みます。

- `bonsai/owarai-live` — お笑い・落語など
- `bonsai/dj-event` — DJイベント

今後 `idol-live` などを同じ正規化形式で追加できます。

## Local run

Python 3.11+ を想定。

```bash
uv run --with mcp python mcp/server.py
```

Claude Desktop / Cursor / Roo / その他 MCP クライアントから stdio サーバーとして接続できます。

## Design

```text
                 ┌─ 🍚 meal
DATE ── LIVE ────┼─ 🎧 / 🎙 / 🎭 event
                 └─ ☕ walk / cafe

event DB → MCP → AI
              ↓
        「この日のデートどうする？」
```

ライブを検索結果の一要素ではなく「デートの時間軸を決めるアンカー」として扱うのがポイントです。

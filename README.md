# OWARAI MUSEN DISCOVERY

お笑いライブを「無料 → 500円以下 → 1,000円以下 → その他」の順で発見する探索エンジン。

> 今日、金をかけずにどこまでお笑いを見られるか？

## Core

- `src/ontology.py` — Event / Query / DiscoveryRun の正規モデル
- `src/memory.py` — Discovery Score と探索履歴
- `src/graph.py` — 芸人・会場・ライブの発見グラフ
- `src/search_engine.py` — 検索クエリ生成レイヤー
- `src/web_discovery.py` — 実Web検索と候補証拠の保存
- `src/discovery_agent.py` — Discover → Score → Expand → Remember のオーケストレータ
- `config/settings.yaml` — 探索上限・スコア重み・情報源
- `.data/events.json` — 現在のライブデータ
- `.data/web-candidates.json` — Web検索で得た未検証候補
- `.data/agent-memory.jsonl` — 実行時メモリ（Git管理外）

## Discovery Loop

```text
Seed
 ↓
Discover（実Web検索）
 ↓
Score
 ↓
Expand（芸人・会場・情報源）
 ↓
Normalize
 ↓
Deduplicate
 ↓
Verify
 ↓
Remember
 ↓
Prioritize
 ↺
```

重要なのは、エージェントが勝手に「正解」を決めることではなく、**発見効率の高い探索経路を学習して次の検索を助けること**。

## Prototype

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m src.web_discovery
python scripts/search_agent.py
```

`src.web_discovery` はAPIキー不要のWeb検索から候補URLを収集し、`.data/web-candidates.json` に証拠として保存する。検索結果だけではイベントを「確認済み」に昇格させず、公式チケット・公式サイト等で再確認する。

## Sources

公式チケット・公式サイトを優先し、無料・低価格・若手・地下ライブまで探索対象にする。GRIP / DASH も除外しない。

候補は「要確認」のまま保持し、`source_url` を失わない。

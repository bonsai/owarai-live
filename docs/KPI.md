# OWARAI MUSEN KPI

> `docs/DB_STRATEGY.md` §7 の成功指標を、計測可能・更新可能な形で管理する。
> 目標は 3 段階: **今週（15日以内）/ P5完了（基準）/ ストレッチ**。週次で更新する。

期間: 2026-09-17 〜（P5完了まで）

| # | KPI | 定義・計測方法 | 現状<br>(2026-09-17) | 今週目標 | P5目標 | 備考 |
|---|-----|----------------|----------------------|----------|--------|------|
| 1 | 表示可能イベント数 (≤500円) | `events.json` + `weekly/*.json` を結合し、priceValue ≤500 かつ date 範囲内のユニーク件数 | **33** | 45 | **60+** | サイト最上部統計と一致させる |
| 2 | Venue Asset 数 | `schema.json` 準拠の `type=venue` ノード数（venue-seeds/halls/domes 統合後） | **~10**（シード） | 20 | **50+** | 領域別カバレッジも目標化 |
| 3 | イベントの Relation 接続率 | `held_at`（会場）または `sold_by`（provider）に接続する Event の割合 | **~0%** | 30% | **100%** | P2 関係配線で計測開始 |
| 4 | 価格判明率 | price_yen（整数）が確定しているイベント / 全イベント | **~80%** (33/41) | 90% | **95%** | 価格不明は表示対象外とする |
| 5 | search-agent PASS 率 | 直近7回の workflow 実行の成功割合 | **0%**（6連敗・修正済み） | 100% | **100%** | 7日連続 PASS を維持 |
| 6 | 販売・情報の重複率 | 同一イベント（provider+id 正規キー）が別キーでも存在する割合 | 検出尺度なし | 導入 | **0%** | P2 dedupe 強化で実装 |
| 7 | 自動収集での新規イベント数/週 | search-agent 1週間で追加された新規イベント数 | 0（停止中） | 5+ | **恒常 ≥5/週** | Fallback 手動収集とも比較 |

## 計測方法

- KPI 1・4・6: リポジトリ内ワンライナー/スクリプトで算出（`.data/events.json` + `weekly/*.json` を同じ `priceValue` ロジックで評価）
- KPI 5: `gh run list --workflow search-agent.yml --limit 7` の conclusion
- KPI 2・3: P1/P2 実装後に `schema.json` 検証 + Relation エッジ集計

## 更新ルール

- 週次（毎週水曜 = 収集実行日）に現状値を更新
- search-agent スケジュールと連動して自動で `docs/KPI.md` へ追記できるよう、計測スクリプトの CI 化を P3 の対象に含める
- 数値が前週比で悪化（例: 表示件数の減少、PASS率100%割れ）したら回帰としてブロッカー化

## KPI 計測のためのスクリプト（提案）

`scripts/measure_kpi.js`（Node any）— `priceValue`/日付範囲を `src/App.vue` と同一ロジックで実装し、
上記 KPI 1・4・6 を `--json` で出力する。P1 で `scripts/` に追加し、ワークフロー週次実行に組み込む。

---

- 上位戦略: `docs/DB_STRATEGY.md`
- 概念: `aw.md`
- 関連 issue: #3 (P0) / #4 (P1) / #5 (P2) / #6 (P3) / #7 (P4) / #8 (P5)
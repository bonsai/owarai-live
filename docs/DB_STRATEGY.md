# OWARAI MUSEN DB 構築戦略（AW: Asset-first Semantic Asset DB）

> 方針: `aw.md`（AW概念）に従い、イベントを「点」で保存せず、**Asset + Relation のグラフ**として構築する。
> 保存契約は `schema.json`、意味契約は `ontology.yaml`（yose-db のパターンを借用・発展）で管理する。

---

## 1. 現状把握（As-Is）

| 分類 | ファイル | 状態 |
|------|----------|------|
| イベント（週次） | `weekly/YYYY-MM-DD.json` | 日別フラット配列。open/start/price の簡易スキーマ。一部イベントは記述スキーマ混在 |
| イベント（過去DB/シード） | `.data/events.json` | `{content:"配列文字列"}` ラッパー。イベント埋め込み式（会場・演者も文字列保持） |
| Asset 軽量版 | `.data/assets.json` | provider×3（tiget/fany/confetti）+ venue 数件。id/type/name/url/capabilities/genres 形式 |
| 会場シード | `.data/venue-seeds.json` | 下北GRIP・新宿末廣亭・国立演芸場など。seed:true、一部住所/URL未確定 |
| 大規模会場 | `domes.json` / `halls.json` | Venue Complex → Hall 階層の構造定義 |
| 演者・イベント行 | `data/comedians.jsonl` / `*.jsonl` | 演者・イベントの行データ |
| 収集 | `src/web_discovery.py` / `scripts/search_agent.py` | 自動ディスカバリ。9/12-17 に **6回連続失敗**（修正済み a3b2542） |
| 正規化 | `src/ontology.py` | Event スキーマ + `price_kind`（free/under_500/under_1000/paid/unknown） |
| 検索 | `src/search_graph.py` / `src/semantic_search.py` | グラフ・セマンティック検索の土台 |
| 設定 | `config/settings.yaml` | sources: TIGET/FANY/カンフェティ/はしご/下北GRIP(DASH) |

**課題**
1. イベントDBはフラット。会場・演者・主催者が **Asset 化されていない**（Relation 未配線）
2. `assets.json` / `venue-seeds.json` / `domes.json` / `halls.json` が **別々に存在し統合されていない**
3. 定常開催（下北GRIP 毎日3部制）を個別イベントとして手動登録している（recurring 化されていない）
4. 価格不明ソース（はしご等）は FIND 専用だが運用ルール未明文化
5. confidence が「確認済み/要確認」の2値。シードと候補の区別が DB 上不明瞭
6. 検索はイベント一覧依存。Relation を使った意味検索（例: 幕張メッセで過去に開催されたイベント）が実現していない

---

## 2. 目標（To-Be）— AW Asset-first DB

```
[Source] → [Collector] → [Normalizer] → [Asset DB] → [Relation] → [Semantic Query] → [Delivery]
  公式HP・TIGET     web_discovery/      schema.json     6種以上        グラフエッジ      search_graph/        App.vue / API /
  FANY・カンフェティ  search_agent       ontology.py     Asset          .jsonl            semantic_search      stage-search → BQML
```

**保存する Asset（独立 Entity）**

| Asset | id 規約 | 備考 |
|-------|---------|------|
| Provider | `provider:{slug}` | TIGET/FANY/カンフェティ… capabilities 保持 |
| Venue Complex | `venue_complex:{slug}` | 幕張メッセ/国立演芸場 など大規模複合 |
| Venue / Hall / Space | `venue:{slug}` | 演者が立つ最小単位の場所。Complex に `part_of` |
| Organizer | `organizer:{slug}` | 主催・運営団体（U&Cエンタプライズ等） |
| Performer | `performer:{slug}` | 芸人・グループ |
| Event Series | `series:{slug}` | 定例・連続公演（RAGS TO RICHES, パワーオブフリー等）→ recurring の実体 |
| Event | `event:{provider}:{provider_id}` | 個別公演。楽チケット正規化で同一イベントを dedupe |
| Ticket | `ticket:{...}` | `price_yen`（整数）。価格帯の唯一の真実 |
| Source | `source:{url-hash}` | 公式URL。provenance（裏付け） |

**Relation（第一級の辺）**

```
Provider ──sells──→ Ticket ──for──→ Event
Organizer ──organizes──→ Event / Series
Performer ──appears_in──→ Event
Event ──held_at──→ Venue/Hall
Venue/Hall ──part_of──→ Venue Complex
Event ──part_of_series──→ Event Series
Asset ──verified_by──→ Source
```

エッジは `relations/{date}.jsonl` 等に別管理し、Asset 本体（ノード）と分離する。
ノードの再発見とエッジの再配線を独立に更新できるようにする。

---

## 3. データモデル契約

### 3.1 保存契約 `schema.json`（ojs）
yose-db の `schema.json` 方式を借用し、`type` を owari 用に拡張する:

```json
{
  "type": "object",
  "required": ["id", "type", "name", "sources"],
  "properties": {
    "id":           {"type": "string"},
    "type":         {"enum": ["provider","venue_complex","venue","organizer","performer","event_series","event","ticket","source"]},
    "name":         {"type": "string"},
    "aliases":      {"type": "array", "items": {"type": "string"}},
    "attributes":   {"type": "object"},
    "relations":    {"type": "object"},
    "sources":      {"type": "array", "items": {"$ref": "#/$defs/source"}},
    "confidence":   {"enum": ["source_confirmed","seed","candidate"]}
  },
  "additionalProperties": false
}
```

### 3.2 意味契約 `ontology.yaml`
yose-db の `ontology.yaml` と同型。classes / properties / relations / patterns / instances を定義し、
`aw.md` の Asset Schema・Relation 図と整合させる（RDF/OWL 変換可能な軽量構造を維持）。

### 3.3 confidence 3段階
| 値 | 意味 | 表示 |
|----|------|------|
| `source_confirmed` | 公式で価格・日時・会場 確認済み（Ticket price_yen あり） | 表示 |
| `seed` | シード/再探索起点。価格未確定 | 表示しない（探索にのみ使用） |
| `candidate` | 候補。VERIFY 待ち | 表示しない（`confidence: 要確認` 相当） |

未確認・価格不明は表示対象に **入れない**。表示可能条件 = `source_confirmed` かつ `price_yen <= 500`.

---

## 4. パイプライン設計

```
① Source seed        config/settings.yaml sources + venue-seeds + recurring 定義
② Collect            web_discovery / search_agent（スケジュール毎日。失敗は検知・通知）
③ Normalize          schema.json へ吸い上げ（価格・日時・会場・URL を必須化）
④ Asset 化           venue/organizer/performer/event_series を id 規約で分離作成
⑤ Verify             Ticket price_yen を公式から確認 → confidence=source_confirmed
⑥ Relate             エッジ生成（held_at/sold_by/organized_by/appears_in）
⑦ Persist            weekly/・.data/ へ確定（履歴は消さず Seed 保持）
⑧ Query / Deliver    search_graph で Relation 検索 → App.vue / API / stage-search
```

**recurring 定常枠**（下北GRIP 等）
- `config/recurring.yaml` に「曜日 × 時刻 × 会場 × 料金=無料/一部」を定義
- 指定期間分を自動展開して monthly/schedule へ出力。休演は FormulaX/カレンダー照合で乖離検知

**dedupe 方針**
- 同一イベント = `provider + provider_id`（TIGET の event id など）を正規キーにする
- 別プロバイダ重複は `title + date + venue` の正規化一致でエッジを張って「同一」扱い（削除しない）

---

## 5. 品質・ガバナンス

- **Provenance 必須**: 全 Asset に `sources[].url`。URL のないイベントは `candidate` 扱い
- **価格の真実は Ticket**: `price_yen` 整数のみ。表示価格・価格帯は Ticket から導出（free/under_500/…）
- **価格不明ソースは FIND 専用**: はしご等は発見にのみ使い、公式（TIGET/FANY/カンフェティ/劇場）で価格確認してから登録
- **自動収集の健全性**: search-agent が毎日 PASS すること（連続失敗はブロッカー）。失敗時はランメンバーへ通知
- **スケジュール**: 収集（毎日 04:45 UTC）→ 正規化 → デプロイ（Pages）の一連を CI で完結

---

## 6. ロードマップ

| Phase | 内容 | 完了基準 |
|-------|------|----------|
| **P0 運用復旧** | search-agent の PASS 確認・失敗通知・週次スナップショット | 7日連続 PASS、表示33件維持 |
| **P1 正規化** | `events.json` を素の配列化 + Event Asset 統一スキーマ。`assets.json`/`venue-seeds.json`/`domes.json`/`halls.json` を `schema.json` に統合 | 全イベントが schema 準拠、venue Asset が一覧として検索可能 |
| **P2 関係配線** | Relation エッジ生成（held_at/sold_by/organized_by/appears_in）+ dedupe 強化 | 全イベントが venue/provider へエッジ接続、同一イベント重複ゼロ |
| **P3 意味検索** | search_graph で「会場×過去イベント」「プロバイダ×無料」等の Relation 検索、価格帯ファセット | UI/API からグラフ探索が可能 |
| **P4 定常展開** | recurring.yaml で下北GRIP 等を毎日自動展開。Series Asset を先行作成 | 週あたり表示件数が現行比 +30%以上 |
| **P5 エコシステム** | stage-search / BQML への正規化出力、API 公開 | 「未来の専門DB（寄席・講談・浪曲・吉本劇場）接続」が可能な構造 |

---

## 7. 成功指標（KPI）

| 指標 | 現状 | 目標（P5完了時） |
|------|------|-----------------|
| 表示 ≤500円 イベント数 | 33 | 60+ |
| Venue Asset 数 | ~10 | 50+（領域別カバレッジ） |
| イベントの Asset/R relation 接続率 | ~0% | 100% |
| 価格判明率（price_yen 確定） | ~60% | 95% |
| search-agent PASS 率 | 0%（6連敗） | 100%（7日連続） |
| 重複率（同一イベント重複エントリ） | 検出尺度なし | 0% |

---

## 8. 関連ドキュメント

- `aw.md` — AW 概念（Asset-first / Semantic Search / Search Graph / 設計原則）
- `repos/yose-db/ontology.yaml` + `schema.json` — 契約の借用元（寄席芸能）
- `docs/LINKS.md` — 収集ルール・Provider 一覧
- `config/settings.yaml` / `config/search-seeds.json` — ソース・用語
- `issues #1`（講談浪曲）/ `#2`（Discovery Engine）— 本戦略の上位ゴール
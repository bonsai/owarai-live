# AW — Semantic Asset Discovery

## Purpose

AW（Agent Work / Agentic Workflow）は、イベントを単純な一覧として扱うのではなく、**意味から検索し、関連するAssetを構造化して再利用する層**とする。

基本フロー:

`自然言語Intent → Semantic Facet → Search Graph → Asset → Relation → Event`

## Asset-first

イベントそのものだけを保存対象にしない。

- Provider
- Venue
- Venue Complex
- Hall / Space
- Organizer
- Performer
- Event
- Ticket
- Source

を独立したAssetとして扱い、Relationで接続する。

## 大規模会場の例

TIGETの `GIGA•GIGA SONIC` イベント情報を入口に、会場情報をAssetとして抽出する。

- Event: GIGA•GIGA SONIC
- Provider: TIGET
- Venue Complex: 幕張メッセ
- Venue / Hall: 幕張メッセ 国際展示場 7-8ホール
- Source: TIGET event detail
- Organizer: 株式会社GALDir Media

イベントと会場を同一レコードに埋め込まず、次のように分離する。

```text
Event
 ├─ held_at ─────→ Venue/Hall
 ├─ part_of ─────→ Venue Complex
 ├─ sold_by ─────→ Provider
 ├─ organized_by → Organizer
 └─ source ──────→ Source
```

## Semantic Search

例えば、ユーザーが

> 大きい会場でアイドルイベントを探す

と入力した場合、AWは文字列一致だけでなく意味へ展開する。

```text
Intent
  ↓
large venue
  ↓
Venue Complex / Hall
  ↓
capacity / scale / hall_count / area
  ↓
Event
  ↓
アイドル
```

また、

> 幕張メッセで過去に開催されたアイドルイベント

なら、

```text
Venue Complex: 幕張メッセ
        ↓
held_at / part_of
        ↓
Event
        ↓
genre: アイドル
```

とグラフを辿る。

## Search Graph

```text
Historical DB
    ↓
Seed
    ↓
Semantic Intent
    ↓
Genre / Price / Time / Provider / Venue
    ↓
Provider / Venue / Organizer / Performer
    ↓
Search Query
    ↓
Candidate
    ↓
Verification
    ↓
Asset
    ↓
Relation
    ↓
Event DB / Now
```

過去DBは削除しない。過去データはDiscovery Seedとして利用し、新しいAsset探索の起点にする。

## Asset Schema

```json
{
  "id": "venue_complex:makuhari-messe",
  "type": "venue_complex",
  "name": "幕張メッセ",
  "aliases": [],
  "parent": null,
  "children": ["venue:makuhari-messe-hall-7-8"],
  "attributes": {
    "scale": "large",
    "city": "千葉市",
    "prefecture": "千葉県"
  },
  "sources": [
    {
      "provider": "TIGET",
      "url": "https://tiget.net/events/522619"
    }
  ],
  "confidence": "source_confirmed"
}
```

## Relation

Assetは単独で完結させず、Relationを検索可能な知識グラフとして扱う。

```text
Provider ──lists────→ Event
Event ──held_at────→ Venue/Hall
Venue/Hall ──part_of→ Venue Complex
Organizer ──organizes→ Event
Performer ──appears_in→ Event
Event ──has_ticket─→ Ticket
Asset ──verified_by─→ Source
```

## 設計原則

1. **Event-firstではなくAsset-first**
2. 会場とイベントを分離する
3. 大規模会場はComplex → Hall → Spaceの階層を持てるようにする
4. Provider / Organizer / Venueを別Entityにする
5. Source URLを必ず保持する
6. Semantic Searchは属性だけでなくRelationを辿る
7. Historical DBを消さずSeedとして使う
8. 未確認情報は候補として保持し、`confidence` を下げる
9. 同一イベント・同一会場の重複はIDとRelationでdedupeする
10. AWの出力は検索結果ではなく、再利用可能な構造化Assetとする

## 目標

AWを、

**「検索するAgent」から「世界のAssetを発見・構造化し、Relationを育てるAgent」へ**

拡張する。

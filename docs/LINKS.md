# OWARAI MUSEN — リンク集

お笑いライブを探すための入口。公式情報を優先し、無料・低価格・若手ライブの発見に使う。

## Providers

### TIGET

https://tiget.net/

ライブ・イベントのチケット販売・購入・予約プラットフォーム。無料イベントを含む低価格公演の発見・価格確認に使う。

### FANY

https://ticket.fany.lol/

吉本興業系の公演を探す公式チケット入口。劇場公演や若手ライブの確認に使う。

### カンフェティ

https://www.confetti-web.com/

劇場・お笑い・演劇など幅広い公演情報を検索。小規模公演の発見にも使う。

### お笑いライブ情報サイト はしご

https://hashigo-live.com/

東京のお笑いライブを横断的に探す入口。会場・日付から候補を広げる探索用。

## Discovery hubs

### お笑いライブ検索

https://owarai-live.com/

東京のお笑いライブを日付・芸人・キーワードから探すための検索入口。

### 下北GRIP

https://www.shimokitagrip2020.com/

### 下北GRIP DASH

https://www.shimokita-dash.com/

### 新宿末廣亭

https://suehirotei.com/

落語・講談などの寄席情報、早朝・深夜寄席の探索対象。

---

## Provider data model

- `provider` = イベントを掲載・販売・予約するサービス
- `source_url` = 個別イベントの出典URL
- `provider_url` = Providerの入口URL
- Providerと会場・主催者・イベントは別ノードとして扱う
- 同一イベントが複数Providerに掲載されても、イベントIDで重複排除する

## 収集ルール

- 公式サイト・公式チケットを最優先
- 無料 → 低価格 → 通常価格の順に発見しやすくする
- 下北GRIP / 下北GRIP DASHも除外しない
- 講談 / 浪曲も探索対象にする
- 候補情報は「要確認」として保持し、確定情報と混ぜない
- 同一公演は重複排除する
- 必ず情報源URLを保存する
- Providerは検索グラフの探索ノードとして利用する

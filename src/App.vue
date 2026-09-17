<script setup>
import { computed, ref } from 'vue'
import rawEvents from '../.data/events.json'

const weeklyModules = import.meta.glob('../weekly/*.json', { eager: true, import: 'default' })
const unwrapEvents = (value) => {
  let current = value
  for (let i = 0; i < 4; i += 1) {
    if (Array.isArray(current)) return current
    if (current && typeof current.content === 'string') {
      try { current = JSON.parse(current.content); continue } catch { return [] }
    }
    return []
  }
  return []
}
const normalize = e => ({
  ...e,
  start_at: e.start_at || e.start || '',
  source_url: e.source_url || e.source || '',
  artists: Array.isArray(e.artists) ? e.artists : []
})
const base = unwrapEvents(rawEvents).map(normalize)
const weekly = Object.values(weeklyModules).flatMap(unwrapEvents).map(normalize)
const byId = new Map(base.map(e => [e.id || `${e.date}-${e.title}-${e.venue}`, e]))
for (const e of weekly) {
  const id = e.id || `${e.date}-${e.title}-${e.venue}`
  byId.set(id, { ...e, id })
}

const priceValue = e => {
  const text = String(e.price ?? '').replace(/,/g, '').trim()
  if (/無料|0円|フリー/i.test(text)) return 0
  if (/^[0-9]+$/.test(text)) return Number(text)
  const values = [...text.matchAll(/[0-9]+円/g)].map(m => Number(m[0].replace(/[^0-9]/g, '')))
  if (!values.length) return null
  return Math.max(...values)
}

const today = '2026-09-17'
const allEvents = [...byId.values()]
const events = allEvents.filter(e => priceValue(e) !== null && priceValue(e) <= 500)
const dates = [...new Set(events.map(e => e.date).filter(Boolean))].sort()
const from = ref(today)
const to = ref('2026-09-20')
const q = ref('')
const venue = ref('')
const price = ref('all')

const venues = computed(() => [...new Set(events.map(e => e.venue).filter(Boolean))].sort())
const dateButtons = computed(() => dates.slice(0, 14))
const filtered = computed(() => events
  .filter(e => e.date >= from.value && e.date <= to.value)
  .filter(e => !q.value || `${e.title} ${e.venue} ${e.artists.join(' ')} ${e.organizer || ''}`.toLowerCase().includes(q.value.toLowerCase()))
  .filter(e => !venue.value || e.venue === venue.value)
  .filter(e => price.value === 'all' || (price.value === 'free' ? priceValue(e) === 0 : priceValue(e) > 0))
  .sort((a, b) => `${a.date}${a.start_at}`.localeCompare(`${b.date}${b.start_at}`))
)

const selectDay = day => { from.value = day; to.value = day }
const selectPeriod = days => {
  from.value = today
  const end = new Date(`${today}T00:00:00+09:00`)
  end.setDate(end.getDate() + days - 1)
  to.value = end.toISOString().slice(0, 10)
}
</script>

<template>
<main class="container">
  <header>
    <div class="eyebrow">TOKYO · OWARAI · DISCOVERY</div>
    <h1>東京お笑いLIVE検索</h1>
    <p>無料〜500円を中心に、今日行けるライブを探す。</p>
    <div class="stats"><span>{{ filtered.length }}件</span><span>{{ venues.length }}会場</span><span>公式リンク優先</span></div>
  </header>

  <nav class="periods" aria-label="期間">
    <button @click="selectDay(today)">今日</button>
    <button @click="selectPeriod(2)">今日〜明日</button>
    <button @click="selectPeriod(4)">今週</button>
    <button @click="selectPeriod(7)">7日間</button>
  </nav>

  <nav class="days" aria-label="日付">
    <button v-for="day in dateButtons" :key="day" :class="{active: from === day && to === day}" @click="selectDay(day)">
      {{ day.slice(5).replace('-', '/') }}
    </button>
  </nav>

  <section class="controls">
    <input v-model="q" placeholder="ライブ名・会場・芸人・主催者を検索" aria-label="検索">
    <div class="filters">
      <select v-model="venue" aria-label="会場">
        <option value="">すべての会場</option>
        <option v-for="name in venues" :key="name" :value="name">{{ name }}</option>
      </select>
      <div class="price-tabs">
        <button :class="{active: price === 'all'}" @click="price='all'">全部</button>
        <button :class="{active: price === 'free'}" @click="price='free'">無料</button>
        <button :class="{active: price === 'paid'}" @click="price='paid'">500円以内</button>
      </div>
    </div>
  </section>

  <section class="result-head">
    <h2>{{ from === to ? from.replaceAll('-', '/') : `${from.replaceAll('-', '/')} — ${to.replaceAll('-', '/')}` }}</h2>
    <button v-if="q || venue || price !== 'all'" class="clear" @click="q='';venue='';price='all'">条件をクリア</button>
  </section>

  <section>
    <article v-for="e in filtered" :key="e.id" class="event">
      <time><b>{{ e.date.slice(5).replace('-', '/') }}</b><br>{{ e.start_at || '時間未定' }}</time>
      <div>
        <h3>{{ e.title }}</h3>
        <p class="venue">📍 {{ e.venue || '会場未定' }}</p>
        <p v-if="e.artists.length" class="artists">{{ e.artists.slice(0, 8).join(' / ') }}<span v-if="e.artists.length > 8"> / ほか</span></p>
        <strong>{{ e.price || '料金未確認' }}</strong>
      </div>
      <a v-if="e.source_url" :href="e.source_url" target="_blank" rel="noreferrer">詳細 ↗</a>
    </article>
    <div v-if="!filtered.length" class="empty">
      <strong>該当するライブがありません。</strong>
      <p>日付を広げるか、会場・検索条件を外してみてください。</p>
    </div>
  </section>

  <footer>
    <p>データは各イベントの出典URLを優先して確認してください。販売状況・出演者・時間・料金は変更される場合があります。</p>
  </footer>
</main>
</template>

<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#171717;background:#f7f7f5}*{box-sizing:border-box}body{margin:0}.container{max-width:820px;margin:auto;padding:22px 16px 70px}header{padding:18px 0 12px}.eyebrow{font-size:.72rem;letter-spacing:.14em;color:#777;font-weight:700}h1{font-size:2rem;line-height:1.1;margin:7px 0}.header p{margin:5px 0;color:#666}.stats{display:flex;gap:7px;margin-top:15px;flex-wrap:wrap}.stats span{background:#fff;border:1px solid #ddd;border-radius:999px;padding:5px 10px;font-size:.78rem}.periods,.days,.filters,.price-tabs{display:flex;gap:7px;align-items:center}.periods{padding:8px 0}.days{overflow:auto;padding:5px 0 14px}.periods button,.days button,.price-tabs button{border:1px solid #ccc;background:#fff;border-radius:8px;padding:8px 11px;white-space:nowrap;cursor:pointer}.periods button:hover,.days button:hover,.price-tabs button:hover,.active{background:#171717!important;color:#fff;border-color:#171717!important}.controls{background:#fff;border:1px solid #ddd;border-radius:12px;padding:12px;margin-bottom:15px}.controls input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:1rem}.filters{margin-top:9px;justify-content:space-between}.filters select{padding:9px;border:1px solid #ccc;border-radius:8px;max-width:55%}.price-tabs{overflow:auto}.price-tabs button{padding:7px 9px}.result-head{display:flex;justify-content:space-between;align-items:center}.result-head h2{font-size:1rem;margin:12px 0}.clear{border:0;background:none;text-decoration:underline;cursor:pointer;color:#666}.event{display:grid;grid-template-columns:100px 1fr auto;gap:14px;align-items:center;background:#fff;border:1px solid #e0e0dc;border-radius:10px;padding:14px;margin:8px 0}.event time{font-size:.82rem;color:#666}.event h3{font-size:1rem;margin:0 0 5px}.event p{margin:0}.venue{color:#555;font-size:.88rem}.artists{color:#777;font-size:.8rem;margin:5px 0!important;line-height:1.45}.event strong{font-size:.85rem}.event a{color:#171717;text-decoration:none;border:1px solid #ccc;border-radius:7px;padding:7px 9px;white-space:nowrap}.empty{background:#fff;border:1px dashed #ccc;border-radius:10px;padding:30px;text-align:center;color:#666}.empty p{margin-bottom:0}footer{margin-top:30px;color:#888;font-size:.72rem;line-height:1.6}@media(max-width:600px){.event{grid-template-columns:65px 1fr}.event a{grid-column:2;width:max-content}.event time{font-size:.72rem}.filters{align-items:flex-start;flex-direction:column}.filters select{max-width:100%;width:100%}.price-tabs{width:100%}h1{font-size:1.7rem}}
</style>

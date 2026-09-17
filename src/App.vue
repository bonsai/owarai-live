<script setup>
import { computed, ref } from 'vue'
import rawEvents from '../.data/events.json'

// Weekly event files are additive overlays. Drop a YYYY-MM-DD.json into weekly/
// and Vite includes it automatically at build time.
const weeklyModules = import.meta.glob('../weekly/*.json', {
  eager: true,
  import: 'default'
})

const unwrapEvents = (value) => {
  let current = value
  for (let i = 0; i < 4; i += 1) {
    if (Array.isArray(current)) return current
    if (current && typeof current.content === 'string') {
      try { current = JSON.parse(current.content); continue } catch { return [] }
    }
    return []
  }
  return Array.isArray(current) ? current : []
}

const normalizeEvent = (e) => ({
  ...e,
  start_at: e.start_at || e.start || '',
  source_url: e.source_url || e.source || '',
  price: e.price ?? ''
})

const baseEvents = unwrapEvents(rawEvents).map(normalizeEvent)
const weeklyEvents = Object.values(weeklyModules)
  .flatMap(unwrapEvents)
  .map(normalizeEvent)

// Weekly data wins on duplicate IDs; existing events.json remains the base dataset.
const eventsById = new Map(baseEvents.map(e => [e.id || `${e.date}-${e.title}-${e.venue}`, e]))
for (const event of weeklyEvents) {
  const id = event.id || `${event.date}-${event.title}-${event.venue}`
  eventsById.set(id, { ...event, id })
}
const allEvents = [...eventsById.values()]

// OWARAI MUSEN: only explicitly free or exactly <=500 yen is eligible.
// Never use the cheapest tier when a price string contains a higher ticket price.
const priceValue = (e) => {
  const text = String(e.price || '').replace(/,/g, '')
  if (/無料|0円|フリー/i.test(text)) return 0
  const values = [...text.matchAll(/[0-9]+円/g)].map(m => Number(m[0].replace(/[^0-9]/g, '')))
  if (!values.length) return null
  if (values.some(v => v > 500)) return null
  return Math.max(...values)
}

const events = allEvents.filter(e => {
  const price = priceValue(e)
  return price !== null && price <= 500
})

const today = '2026-09-17'
const from = ref(today)
const to = ref('2026-09-20')
const area = ref('')
const q = ref('')
const freeOnly = ref(false)
const genre = ref('')
const genres = ['漫才・コント', 'スタンダップコメディ', '寄席', '落語', '講談', '浪曲']
const areas = computed(() => [...new Set(events.map(e => e.area).filter(Boolean))].sort())
const performers = computed(() => [...new Set(events.flatMap(e => e.artists || []).filter(Boolean)).sort((a,b)=>a.localeCompare(b,'ja')).slice(0,80))

const matchesGenre = (e) => {
  if (!genre.value) return true
  const text = `${e.title} ${e.note || ''} ${e.source_type || ''}`
  const aliases = {
    '漫才・コント': /漫才|コント|ネタ|お笑い/,
    'スタンダップコメディ': /スタンダップ|stand.?up|standup/i,
    '寄席': /寄席|昼寄席|夜寄席|落語会/,
    '落語': /落語|らくご/,
    '講談': /講談/,
    '浪曲': /浪曲/
  }
  return aliases[genre.value]?.test(text) ?? false
}

const filtered = computed(() => events
  .filter(e => e.date >= from.value && e.date <= to.value)
  .filter(e => !area.value || e.area === area.value)
  .filter(matchesGenre)
  .filter(e => !freeOnly.value || priceValue(e) === 0)
  .filter(e => !q.value || `${e.title} ${e.venue} ${(e.artists || []).join(' ')}`.toLowerCase().includes(q.value.toLowerCase()))
  .sort((a,b) => `${a.date}${a.start_at||''}`.localeCompare(`${b.date}${b.start_at||''}`))
)

const todayEvents = computed(() => events
  .filter(e => e.date === today)
  .filter(e => !freeOnly.value || priceValue(e) === 0)
  .sort((a,b) => (a.start_at||'').localeCompare(b.start_at||''))
  .slice(0,8)
)

const cheapEvents = computed(() => events
  .filter(e => e.date >= today)
  .sort((a,b) => `${a.date}${a.start_at||''}`.localeCompare(`${b.date}${b.start_at||''}`))
  .slice(0,12)
)

function searchArtist(name) { q.value=name; from.value=today; to.value='2026-12-31' }
function setFree() { freeOnly.value=true }
function setAll() { freeOnly.value=false }
</script>

<template>
<main class="container">
<header class="hero">
  <p class="eyebrow">OWARAI MUSEN 📡</p>
  <h1>500円以下で探す<br>東京の笑いLIVE</h1>
  <p class="lead">漫才・コントだけじゃない。スタンダップコメディ、寄席、落語、講談、浪曲まで。無料〜500円だけを探す。</p>
  <div class="quick">
    <button @click="from=today;to=today;genre='';setAll()">🔥 今日の500円以下</button>
    <button @click="from=today;to=today;genre='';setFree()">🆓 今日の無料</button>
    <button @click="from=today;to=today;genre='寄席';setAll()">🏮 寄席</button>
    <button @click="from=today;to=today;genre='スタンダップコメディ';setAll()">🎤 スタンダップ</button>
  </div>
</header>

<section class="panel filters">
  <h2>🔎 500円以下だけ探す</h2>
  <div class="price-tabs">
    <button class="active" @click="setAll()">500円以下</button>
    <button :class="{active:freeOnly}" @click="setFree()">🆓 無料</button>
  </div>
  <div class="genres">
    <button :class="{active:!genre}" @click="genre=''">すべて</button>
    <button v-for="g in genres" :key="g" :class="{active:genre===g}" @click="genre=g">{{g}}</button>
  </div>
  <div class="grid">
    <label>開始日<input v-model="from" type="date"></label>
    <label>終了日<input v-model="to" type="date"></label>
    <label>エリア<select v-model="area"><option value="">すべて</option><option v-for="a in areas" :key="a">{{a}}</option></select></label>
    <label>キーワード<input v-model="q" placeholder="芸人・ライブ・会場"></label>
  </div>
  <label class="check"><input v-model="freeOnly" type="checkbox"> 完全無料だけ表示</label>
</section>

<section class="agent panel"><strong>📡 OWARAI MUSEN Search Agent</strong><span>500円以下限定 / 無料 / 漫才・コント / スタンダップ / 寄席 / 落語 / 講談 / 浪曲 / 公式情報優先</span></section>

<section class="panel">
  <div class="section-head"><h2>🔥 今日の500円以下</h2><span>{{todayEvents.length}}件</span></div>
  <div class="mini-grid"><article v-for="e in todayEvents" :key="e.id" class="mini-card"><b>{{e.start_at||'時間確認'}}</b><strong>{{e.title}}</strong><small>📍 {{e.venue}} · {{e.price}}</small></article></div>
</section>

<section class="panel">
  <div class="section-head"><h2>💸 500円以下の笑い</h2><span>無料〜500円</span></div>
  <div class="mini-grid"><article v-for="e in cheapEvents" :key="e.id" class="mini-card cheap"><b>{{e.date}} {{e.start_at||''}}</b><strong>{{e.title}}</strong><small>{{e.price}} · {{e.venue}}</small></article></div>
</section>

<section class="panel"><div class="section-head"><h2>🎤 芸人から探す</h2><span>{{performers.length}}人</span></div><div class="chips"><button v-for="name in performers" :key="name" @click="searchArtist(name)">{{name}}</button></div></section>

<section class="results">
  <div class="summary">{{filtered.length}}件 · {{from}}〜{{to}} · {{genre||'全ジャンル'}} · {{freeOnly?'無料':'500円以下'}}</div>
  <article v-for="e in filtered" :key="e.id" class="card">
    <div class="date">{{e.date}}<br><b>{{e.start_at||'時間確認'}}</b></div>
    <div class="body"><h2>{{e.title}}</h2><p class="artists">{{(e.artists||[]).join(' / ')}}</p><p>📍 {{e.venue}} · {{e.area}}</p><div class="badges"><span class="badge">{{e.price}}</span><span class="badge muted">{{e.source_type}}</span><span class="badge muted">{{e.confidence}}</span></div><p class="note">{{e.note}}</p><a :href="e.source_url" target="_blank" rel="noreferrer">情報源 ↗</a></div>
  </article>
  <div v-if="!filtered.length" class="empty">500円以下の該当ライブなし。探索エージェントの検索網を広げよう。</div>
</section>
<footer>OWARAI MUSEN · 無料〜500円の笑いを見つける探索網</footer>
</main>
</template>

<style>
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#171717;background:#f5f2ea}*{box-sizing:border-box}body{margin:0}.container{max-width:1100px;margin:auto;padding:24px 18px 60px}.hero{padding:28px 0 22px}.eyebrow{font-weight:900;letter-spacing:.12em}.hero h1{font-size:clamp(2.2rem,7vw,5rem);line-height:.95;margin:10px 0 18px}.lead{font-size:1.05rem;max-width:760px}.quick,.chips,.genres,.price-tabs{display:flex;gap:8px;flex-wrap:wrap}.quick button,.chips button,.genres button,.price-tabs button{border:1px solid #222;background:#fff;padding:9px 13px;border-radius:999px;cursor:pointer}.price-tabs{margin:12px 0 8px}.price-tabs button{font-weight:800}.price-tabs button.active,.genres button.active{background:#171717;color:#fff}.genres{margin:12px 0 16px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}label{display:flex;flex-direction:column;gap:5px;font-size:.85rem;font-weight:700}input,select{padding:10px;border:1px solid #999;border-radius:9px;background:#fff}.check{margin-top:12px;display:block}.agent{display:flex;gap:16px;align-items:center;flex-wrap:wrap;background:#161616;color:#fff;border-color:#161616;box-shadow:none}.section-head{display:flex;justify-content:space-between;align-items:center}.section-head h2{margin:0}.mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}.mini-card{border:1px solid #ccc;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:5px}.mini-card strong{line-height:1.25}.mini-card small{color:#666}.cheap{border-left:5px solid #111}.summary{font-weight:800;margin:22px 0 10px}.card{display:grid;grid-template-columns:110px 1fr;gap:18px;background:#fff;border:1px solid #ccc;border-radius:14px;padding:16px;margin:10px 0}.date{font-size:.9rem}.body h2{margin:0 0 8px}.artists{font-weight:700}.badges{display:flex;gap:6px;flex-wrap:wrap}.badge{display:inline-block;border-radius:999px;padding:4px 9px;background:#eee;font-size:.8rem}.muted{opacity:.65}.note{color:#666}.body a{font-weight:800;color:#111}.empty{padding:30px;background:#fff;border-radius:14px}footer{text-align:center;color:#666;margin-top:35px}@media(max-width:760px){.grid{grid-template-columns:1fr 1fr}.mini-grid{grid-template-columns:1fr 1fr}.card{grid-template-columns:1fr}.hero h1{font-size:3rem}}@media(max-width:480px){.grid,.mini-grid{grid-template-columns:1fr}.container{padding:14px}}
</style>

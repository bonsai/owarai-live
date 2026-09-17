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
const normalize = e => ({ ...e, start_at: e.start_at || e.start || '', source_url: e.source_url || e.source || '' })
const base = unwrapEvents(rawEvents).map(normalize)
const weekly = Object.values(weeklyModules).flatMap(unwrapEvents).map(normalize)
const byId = new Map(base.map(e => [e.id || `${e.date}-${e.title}-${e.venue}`, e]))
for (const e of weekly) { const id = e.id || `${e.date}-${e.title}-${e.venue}`; byId.set(id, { ...e, id }) }
const priceValue = e => {
  const text = String(e.price || '').replace(/,/g, '')
  if (/無料|0円|フリー/i.test(text)) return 0
  const values = [...text.matchAll(/[0-9]+円/g)].map(m => Number(m[0].replace(/[^0-9]/g, '')))
  if (!values.length || values.some(v => v > 500)) return null
  return Math.max(...values)
}
const events = [...byId.values()].filter(e => priceValue(e) !== null && priceValue(e) <= 500)
const today = '2026-09-17'
const from = ref(today), to = ref('2026-09-20'), q = ref('')
const filtered = computed(() => events.filter(e => e.date >= from.value && e.date <= to.value).filter(e => !q.value || `${e.title} ${e.venue} ${(e.artists || []).join(' ')}`.toLowerCase().includes(q.value.toLowerCase())).sort((a,b) => `${a.date}${a.start_at}`.localeCompare(`${b.date}${b.start_at}`)))
</script>

<template>
<main class="container">
  <header><h1>東京お笑いLIVE</h1><p>無料〜500円</p></header>
  <nav class="days">
    <button v-for="day in ['2026-09-17','2026-09-18','2026-09-19','2026-09-20']" :key="day" @click="from=day;to=day">{{day.slice(5).replace('-', '/')}}</button>
  </nav>
  <div class="search"><input v-model="q" placeholder="ライブ・会場・芸人を検索"></div>
  <section><article v-for="e in filtered" :key="e.id" class="event">
    <time>{{e.date}} {{e.start_at || ''}}</time>
    <div><h2>{{e.title}}</h2><p>{{e.venue}}</p><strong>{{e.price}}</strong></div>
    <a v-if="e.source_url" :href="e.source_url" target="_blank" rel="noreferrer">詳細</a>
  </article><p v-if="!filtered.length">該当するライブはありません。</p></section>
</main>
</template>

<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#222;background:#fff}*{box-sizing:border-box}body{margin:0}.container{max-width:760px;margin:auto;padding:24px 16px 60px}header{padding:20px 0}h1{font-size:2rem;margin:0}header p{margin:4px 0;color:#777}.days{display:flex;gap:6px;overflow:auto;padding:8px 0 14px}.days button{white-space:nowrap;border:1px solid #ccc;background:#fff;border-radius:6px;padding:8px 12px;cursor:pointer}.search input{width:100%;padding:11px;border:1px solid #ccc;border-radius:6px;margin-bottom:12px}.event{display:grid;grid-template-columns:105px 1fr auto;gap:14px;align-items:center;border-top:1px solid #ddd;padding:14px 2px}.event time{font-size:.85rem;color:#666}.event h2{font-size:1rem;margin:0 0 5px}.event p{margin:0 0 4px;color:#666}.event strong{font-size:.9rem}.event a{color:#222;text-decoration:none;border:1px solid #ccc;border-radius:5px;padding:6px 9px}@media(max-width:520px){.event{grid-template-columns:72px 1fr}.event a{grid-column:2;width:max-content}.event time{font-size:.75rem}}
</style>

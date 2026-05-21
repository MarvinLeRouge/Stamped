<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import api from '@/api'
import { useElevationStore, type ElevationPoint } from '@/stores/elevation'
import { useHighlightStore } from '@/stores/highlight'
import { useQuestsStore } from '@/stores/quests'

const PAD = { top: 12, right: 16, bottom: 24, left: 48 }
const W = 800
const H = 140

const questsStore = useQuestsStore()
const elevationStore = useElevationStore()
const highlightStore = useHighlightStore()

const svgEl = ref<SVGSVGElement | null>(null)
const hoverX = ref<number | null>(null)
const hoverPoint = ref<ElevationPoint | null>(null)

const pts = computed(() => elevationStore.points)

const minAlt = computed(() => Math.min(...pts.value.map((p) => p.alt)))
const maxAlt = computed(() => Math.max(...pts.value.map((p) => p.alt)))
const maxD = computed(() => pts.value.at(-1)?.d ?? 1)

function px(d: number): number {
  return PAD.left + (d / maxD.value) * (W - PAD.left - PAD.right)
}

function py(alt: number): number {
  const range = maxAlt.value - minAlt.value || 1
  return PAD.top + (1 - (alt - minAlt.value) / range) * (H - PAD.top - PAD.bottom)
}

const polyline = computed(() => pts.value.map((p) => `${px(p.d)},${py(p.alt)}`).join(' '))

const area = computed(() => {
  if (!pts.value.length) return ''
  const bottom = H - PAD.bottom
  const first = `${px(pts.value[0]!.d)},${bottom}`
  const last = `${px(pts.value.at(-1)!.d)},${bottom}`
  return `${first} ${polyline.value} ${last}`
})

// Highlight point driven by Storyline hover (hoveredTimestamp)
const highlightedX = computed(() => {
  const t = highlightStore.hoveredTimestamp
  if (!t || !pts.value.length) return null
  const ts = new Date(t).getTime()
  let closest = pts.value[0]!
  let minDiff = Math.abs(new Date(closest.t).getTime() - ts)
  for (const p of pts.value) {
    const diff = Math.abs(new Date(p.t).getTime() - ts)
    if (diff < minDiff) {
      minDiff = diff
      closest = p
    }
  }
  return px(closest.d)
})

// Y labels
const yLabels = computed(() => {
  if (!pts.value.length) return []
  const range = maxAlt.value - minAlt.value
  const step = range > 500 ? 200 : range > 200 ? 100 : range > 50 ? 50 : 20
  const labels = []
  const start = Math.ceil(minAlt.value / step) * step
  for (let v = start; v <= maxAlt.value; v += step) {
    labels.push({ y: py(v), label: `${Math.round(v)}m` })
  }
  return labels
})

// X labels (distance)
const xLabels = computed(() => {
  if (!pts.value.length) return []
  const totalKm = maxD.value / 1000
  const step = totalKm > 20 ? 5 : totalKm > 10 ? 2 : totalKm > 5 ? 1 : 0.5
  const stepM = step * 1000
  const labels = []
  for (let d = stepM; d < maxD.value; d += stepM) {
    labels.push({ x: px(d), label: `${(d / 1000).toFixed(1)}km` })
  }
  return labels
})

function onMousemove(e: MouseEvent): void {
  if (!svgEl.value || !pts.value.length) return
  const rect = svgEl.value.getBoundingClientRect()
  const relX = ((e.clientX - rect.left) / rect.width) * W
  const d = ((relX - PAD.left) / (W - PAD.left - PAD.right)) * maxD.value
  let closest = pts.value[0]!
  let minDiff = Math.abs(closest.d - d)
  for (const p of pts.value) {
    const diff = Math.abs(p.d - d)
    if (diff < minDiff) {
      minDiff = diff
      closest = p
    }
  }
  hoverX.value = px(closest.d)
  hoverPoint.value = closest
  // Sync with highlight store via timestamp — MapView and Storyline will react
  highlightStore.highlight(null, closest.t)
}

function onMouseleave(): void {
  hoverX.value = null
  hoverPoint.value = null
  highlightStore.highlight(null, null)
}

watch(
  () => questsStore.selectedQuestId,
  async (id) => {
    elevationStore.setPoints([])
    if (id === null) return
    const quest = questsStore.quests.find((q) => q.id === id)
    if (!quest?.has_gpx) return
    elevationStore.setLoading(true)
    try {
      const { data } = await api.get<ElevationPoint[]>(`/quests/${id}/elevation`)
      elevationStore.setPoints(data)
    } finally {
      elevationStore.setLoading(false)
    }
  },
  { immediate: true },
)
</script>

<template>
  <div v-if="elevationStore.visible && pts.length > 0" class="elevation-panel">
    <div class="elevation-panel__inner">
      <svg
        ref="svgEl"
        class="elevation-panel__svg"
        :viewBox="`0 0 ${W} ${H}`"
        preserveAspectRatio="none"
        @mousemove="onMousemove"
        @mouseleave="onMouseleave"
      >
        <!-- Area fill -->
        <polygon :points="area" class="elev-area" />

        <!-- Profile line -->
        <polyline :points="polyline" class="elev-line" />

        <!-- Y grid lines + labels -->
        <g v-for="l in yLabels" :key="l.label">
          <line :x1="PAD.left" :x2="W - PAD.right" :y1="l.y" :y2="l.y" class="elev-grid" />
          <text :x="PAD.left - 4" :y="l.y + 4" class="elev-label-y">{{ l.label }}</text>
        </g>

        <!-- X distance labels -->
        <text
          v-for="l in xLabels"
          :key="l.label"
          :x="l.x"
          :y="H - PAD.bottom + 14"
          class="elev-label-x"
        >
          {{ l.label }}
        </text>

        <!-- Storyline hover → highlight on profile -->
        <line
          v-if="highlightedX !== null"
          :x1="highlightedX"
          :x2="highlightedX"
          :y1="PAD.top"
          :y2="H - PAD.bottom"
          class="elev-cursor elev-cursor--storyline"
        />

        <!-- Mouse hover cursor -->
        <g v-if="hoverX !== null">
          <line :x1="hoverX" :x2="hoverX" :y1="PAD.top" :y2="H - PAD.bottom" class="elev-cursor" />
          <text :x="hoverX + 4" :y="PAD.top + 10" class="elev-tooltip">
            {{ hoverPoint?.alt !== undefined ? Math.round(hoverPoint.alt) + 'm' : '' }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.elevation-panel {
  height: 160px;
  flex-shrink: 0;
  background: #0e0e22;
  border-top: 1px solid #2a2a4e;
  overflow: hidden;
}

.elevation-panel__inner {
  height: 100%;
  padding: 0 0.5rem;
  display: flex;
  align-items: stretch;
}

.elevation-panel__svg {
  width: 100%;
  height: 100%;
  cursor: crosshair;
}

.elev-area {
  fill: #e85d0422;
}

.elev-line {
  fill: none;
  stroke: #e85d04;
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}

.elev-grid {
  stroke: #2a2a4e;
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}

.elev-label-y {
  fill: #666;
  font-size: 9px;
  text-anchor: end;
  font-family: monospace;
}

.elev-label-x {
  fill: #666;
  font-size: 9px;
  text-anchor: middle;
  font-family: monospace;
}

.elev-cursor {
  stroke: #e85d04;
  stroke-width: 1;
  stroke-dasharray: 3 2;
  vector-effect: non-scaling-stroke;
}

.elev-cursor--storyline {
  stroke: #6366f1;
}

.elev-tooltip {
  fill: #ccc;
  font-size: 10px;
  font-family: monospace;
}
</style>

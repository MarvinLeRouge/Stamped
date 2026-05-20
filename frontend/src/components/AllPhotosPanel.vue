<script setup lang="ts">
import { ref, watch } from 'vue'

import api from '@/api'
import { useLightboxStore } from '@/stores/lightbox'
import { useQuestsStore } from '@/stores/quests'

interface Photo {
  id: number
  captured_at: string | null
  thumb_status: string
  is_orphan: boolean
  quest_id: number | null
}

const questsStore = useQuestsStore()
const lightboxStore = useLightboxStore()

const photos = ref<Photo[]>([])
const loading = ref(false)
const filterOrphan = ref<'all' | 'orphan' | 'placed'>('all')

function formatDate(capturedAt: string | null): string {
  if (!capturedAt) return '—'
  return new Date(capturedAt).toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

async function loadPhotos(): Promise<void> {
  loading.value = true
  try {
    const params = new URLSearchParams({ limit: '500' })
    if (filterOrphan.value === 'orphan') params.set('orphan', 'true')
    if (filterOrphan.value === 'placed') params.set('orphan', 'false')
    const { data } = await api.get<Photo[]>(`/photos?${params}`)
    photos.value = data
  } finally {
    loading.value = false
  }
}

watch(
  () => questsStore.showAllPhotos,
  (show) => {
    if (show) loadPhotos()
    else photos.value = []
  },
  { immediate: true },
)

watch(filterOrphan, () => {
  if (questsStore.showAllPhotos) loadPhotos()
})
</script>

<template>
  <aside v-if="questsStore.showAllPhotos" class="all-photos">
    <div class="all-photos__header">
      <h2 class="all-photos__title">Toutes les photos</h2>
      <div class="all-photos__filters">
        <button
          class="all-photos__filter"
          :class="{ 'all-photos__filter--active': filterOrphan === 'all' }"
          @click="filterOrphan = 'all'"
        >
          Toutes
        </button>
        <button
          class="all-photos__filter"
          :class="{ 'all-photos__filter--active': filterOrphan === 'placed' }"
          @click="filterOrphan = 'placed'"
        >
          Placées
        </button>
        <button
          class="all-photos__filter"
          :class="{ 'all-photos__filter--active': filterOrphan === 'orphan' }"
          @click="filterOrphan = 'orphan'"
        >
          Orphelines
        </button>
      </div>
    </div>

    <p v-if="loading" class="all-photos__msg">Loading…</p>
    <p v-else-if="photos.length === 0" class="all-photos__msg">No photos.</p>

    <ul v-else class="all-photos__list">
      <li
        v-for="photo in photos"
        :key="photo.id"
        class="all-photos__item"
        @click="photo.thumb_status === 'done' && lightboxStore.open(photo.id)"
      >
        <div class="all-photos__thumb-wrap">
          <img
            v-if="photo.thumb_status === 'done'"
            :src="`/api/photos/${photo.id}/thumb`"
            class="all-photos__thumb"
            alt="photo"
          />
          <div v-else class="all-photos__thumb all-photos__thumb--pending">…</div>
        </div>
        <div class="all-photos__info">
          <span class="all-photos__date">{{ formatDate(photo.captured_at) }}</span>
          <span v-if="photo.is_orphan" class="all-photos__tag all-photos__tag--orphan">
            orphan
          </span>
          <span v-if="photo.quest_id === null" class="all-photos__tag all-photos__tag--noquest">
            sans quest
          </span>
        </div>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.all-photos {
  min-width: 220px;
  max-width: 340px;
  background: #0e0e22;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-left: 1px solid #2a2a4e;
}

.all-photos__header {
  padding: 0.55rem 0.75rem 0.45rem;
  border-bottom: 1px solid #2a2a4e;
  flex-shrink: 0;
}

.all-photos__title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #ccc;
  margin-bottom: 0.4rem;
}

.all-photos__filters {
  display: flex;
  gap: 0.3rem;
}

.all-photos__filter {
  background: none;
  border: 1px solid #3a3a5e;
  border-radius: 3px;
  color: #888;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 2px 6px;
  transition: all 0.15s;
}

.all-photos__filter:hover {
  color: #ccc;
  border-color: #5a5a8e;
}

.all-photos__filter--active {
  background: #3b3b6e;
  border-color: #6a6aae;
  color: white;
}

.all-photos__msg {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #888;
}

.all-photos__list {
  list-style: none;
  overflow-y: auto;
  flex: 1;
}

.all-photos__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #1a1a30;
  cursor: pointer;
  transition: background 0.15s;
}

.all-photos__item:hover {
  background: #1e1e3a;
}

.all-photos__thumb-wrap {
  flex-shrink: 0;
}

.all-photos__thumb {
  display: block;
  width: 56px;
  height: 42px;
  object-fit: cover;
  border-radius: 3px;
  cursor: pointer;
}

.all-photos__thumb--pending {
  width: 56px;
  height: 42px;
  background: #2a2a4e;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: #666;
}

.all-photos__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.all-photos__date {
  font-size: 0.8rem;
  color: #999;
  line-height: 1.3;
  word-break: break-all;
}

.all-photos__tag {
  font-size: 0.75rem;
  padding: 1px 5px;
  border-radius: 2px;
  font-weight: 600;
  align-self: flex-start;
}

.all-photos__tag--orphan {
  background: #f59e0b22;
  color: #f59e0b;
}

.all-photos__tag--noquest {
  background: #6366f122;
  color: #818cf8;
}
</style>

<script setup lang="ts">
import { ref, watch } from 'vue'

import api from '@/api'
import { useLightboxStore } from '@/stores/lightbox'
import { usePlacementStore } from '@/stores/placement'
import { useQuestsStore } from '@/stores/quests'
import { useStatusStore } from '@/stores/status'

interface UnquestedPhoto {
  id: number
  captured_at: string | null
  thumb_status: string
  is_orphan: boolean
}

const questsStore = useQuestsStore()
const lightboxStore = useLightboxStore()
const placementStore = usePlacementStore()
const statusStore = useStatusStore()

const photos = ref<UnquestedPhoto[]>([])
const loading = ref(false)

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

async function deletePhoto(photoId: number): Promise<void> {
  await api.delete(`/photos/${photoId}`)
  photos.value = photos.value.filter((p) => p.id !== photoId)
  await statusStore.fetch()
}

async function loadPhotos(): Promise<void> {
  loading.value = true
  try {
    const { data } = await api.get<UnquestedPhoto[]>('/photos?no_quest=true&limit=500')
    photos.value = data
  } finally {
    loading.value = false
  }
}

watch(
  () => questsStore.showUnquested,
  (show) => {
    if (show) loadPhotos()
    else {
      photos.value = []
      placementStore.cancel()
    }
  },
  { immediate: true },
)
</script>

<template>
  <aside v-if="questsStore.showUnquested" class="unquested">
    <div class="unquested__header">
      <h2 class="unquested__title">Sans quest</h2>
    </div>

    <p v-if="loading" class="unquested__msg">Loading…</p>
    <p v-else-if="photos.length === 0" class="unquested__msg">No photos.</p>

    <ul v-else class="unquested__list">
      <li v-for="photo in photos" :key="photo.id" class="unquested__item">
        <div class="unquested__thumb-wrap">
          <img
            v-if="photo.thumb_status === 'done'"
            :src="`/api/photos/${photo.id}/thumb`"
            class="unquested__thumb"
            alt="photo"
            @click="lightboxStore.open(photo.id)"
          />
          <div v-else class="unquested__thumb unquested__thumb--pending">…</div>
        </div>
        <div class="unquested__info">
          <span class="unquested__date">{{ formatDate(photo.captured_at) }}</span>
          <div class="unquested__actions">
            <button
              class="unquested__action-btn unquested__action-btn--pin"
              :class="{
                'unquested__action-btn--active': placementStore.placingPhotoId === photo.id,
                'unquested__action-btn--placed': !photo.is_orphan,
              }"
              title="Place on map"
              @click="placementStore.startPlacing(photo.id)"
            >
              📍
            </button>
            <button
              class="unquested__action-btn unquested__action-btn--danger"
              title="Delete photo"
              @click="deletePhoto(photo.id)"
            >
              ✕
            </button>
          </div>
        </div>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.unquested {
  min-width: 180px;
  max-width: 280px;
  background: #111128;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-left: 1px solid #2a2a4e;
}

.unquested__header {
  display: flex;
  align-items: center;
  padding: 0.55rem 0.75rem 0.45rem;
  border-bottom: 1px solid #2a2a4e;
  flex-shrink: 0;
  min-height: 2.1rem;
}

.unquested__title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #ccc;
}

.unquested__msg {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #888;
}

.unquested__list {
  list-style: none;
  overflow-y: auto;
  flex: 1;
}

.unquested__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #1e1e38;
}

.unquested__thumb-wrap {
  flex-shrink: 0;
}

.unquested__thumb {
  display: block;
  width: 56px;
  height: 42px;
  object-fit: cover;
  border-radius: 3px;
  cursor: pointer;
}

.unquested__thumb--pending {
  width: 56px;
  height: 42px;
  background: #2a2a4e;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: #666;
  cursor: default;
}

.unquested__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.unquested__date {
  font-size: 0.8rem;
  color: #999;
  line-height: 1.3;
  word-break: break-all;
}

.unquested__actions {
  display: flex;
  gap: 0.2rem;
}

.unquested__action-btn {
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 0.75rem;
  width: 1.4rem;
  height: 1.4rem;
  padding: 0;
  border-radius: 50%;
  opacity: 0.5;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition:
    opacity 0.15s,
    border-color 0.15s;
}

.unquested__action-btn:hover {
  opacity: 1;
}

.unquested__action-btn--pin:hover {
  border-color: #c0392b;
  background: #2a1a1e;
}

.unquested__action-btn--pin.unquested__action-btn--placed {
  opacity: 1;
}

.unquested__action-btn--active {
  opacity: 1;
  background: #3b1a22;
  border-color: #c0392b;
}

.unquested__action-btn--danger {
  color: #e06c75;
  font-weight: 700;
}

.unquested__action-btn--danger:hover {
  background: #2a1a1e;
  border-color: #c0392b;
  color: #ff6b6b;
}
</style>

<script setup lang="ts">
import { ref, watch } from 'vue'

import api from '@/api'
import { useLightboxStore } from '@/stores/lightbox'
import { useQuestsStore } from '@/stores/quests'

interface StorylinePhoto {
  id: number
  captured_at: string | null
  thumb_status: string
  is_orphan: boolean
}

const questsStore = useQuestsStore()
const lightboxStore = useLightboxStore()

const photos = ref<StorylinePhoto[]>([])
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

watch(
  () => questsStore.selectedQuestId,
  async (id) => {
    photos.value = []
    if (id === null) return
    loading.value = true
    try {
      const { data } = await api.get<StorylinePhoto[]>(`/quests/${id}/photos`)
      photos.value = data
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
</script>

<template>
  <aside v-if="questsStore.selectedQuestId !== null" class="storyline">
    <h2 class="storyline__title">Storyline</h2>

    <p v-if="loading" class="storyline__msg">Loading…</p>
    <p v-else-if="photos.length === 0" class="storyline__msg">No photos.</p>

    <ul v-else class="storyline__list">
      <li v-for="(photo, i) in photos" :key="photo.id" class="storyline__item">
        <span class="storyline__index">{{ i + 1 }}</span>
        <div class="storyline__thumb-wrap">
          <img
            v-if="photo.thumb_status === 'done'"
            :src="`/api/photos/${photo.id}/thumb`"
            class="storyline__thumb"
            alt="photo"
            @click="lightboxStore.open(photo.id)"
          />
          <div v-else class="storyline__thumb storyline__thumb--pending">…</div>
        </div>
        <span class="storyline__date">{{ formatDate(photo.captured_at) }}</span>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.storyline {
  width: 220px;
  background: #111128;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  border-left: 1px solid #2a2a4e;
}

.storyline__title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #aaa;
  padding: 0.75rem 1rem 0.5rem;
  border-bottom: 1px solid #2a2a4e;
  flex-shrink: 0;
}

.storyline__msg {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #888;
}

.storyline__list {
  list-style: none;
  overflow-y: auto;
  flex: 1;
}

.storyline__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #1e1e38;
}

.storyline__index {
  font-size: 0.65rem;
  font-weight: 700;
  color: #666;
  min-width: 1.2rem;
  text-align: right;
  flex-shrink: 0;
}

.storyline__thumb-wrap {
  flex-shrink: 0;
}

.storyline__thumb {
  display: block;
  width: 56px;
  height: 42px;
  object-fit: cover;
  border-radius: 3px;
  cursor: pointer;
}

.storyline__thumb--pending {
  width: 56px;
  height: 42px;
  background: #2a2a4e;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  color: #666;
  cursor: default;
}

.storyline__date {
  font-size: 0.65rem;
  color: #999;
  line-height: 1.3;
  word-break: break-all;
}
</style>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import api from '@/api'
import { useLightboxStore } from '@/stores/lightbox'
import { usePlacementStore } from '@/stores/placement'
import { useQuestsStore } from '@/stores/quests'

interface StorylinePhoto {
  id: number
  captured_at: string | null
  thumb_status: string
  is_orphan: boolean
}

const questsStore = useQuestsStore()
const lightboxStore = useLightboxStore()
const placementStore = usePlacementStore()

const photos = ref<StorylinePhoto[]>([])
const loading = ref(false)

const editing = ref(false)
const editValue = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

const selectedQuest = computed(
  () => questsStore.quests.find((q) => q.id === questsStore.selectedQuestId) ?? null,
)

function questLabel(): string {
  if (!selectedQuest.value) return 'Storyline'
  return selectedQuest.value.name ?? selectedQuest.value.auto_name
}

async function startEdit(): Promise<void> {
  if (!selectedQuest.value) return
  editValue.value = selectedQuest.value.name ?? ''
  editing.value = true
  await nextTick()
  inputRef.value?.select()
}

function cancelEdit(): void {
  editing.value = false
}

async function commitEdit(): Promise<void> {
  if (!questsStore.selectedQuestId) return
  editing.value = false
  const trimmed = editValue.value.trim()
  await questsStore.renameQuest(questsStore.selectedQuestId, trimmed || null)
}

function onInputKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter') commitEdit()
  if (e.key === 'Escape') cancelEdit()
}

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
}

watch(
  () => questsStore.selectedQuestId,
  async (id) => {
    photos.value = []
    editing.value = false
    placementStore.cancel()
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
    <div class="storyline__header">
      <template v-if="editing">
        <input
          ref="inputRef"
          v-model="editValue"
          class="storyline__name-input"
          @keydown="onInputKeydown"
          @blur="commitEdit"
        />
      </template>
      <template v-else>
        <h2 class="storyline__title">{{ questLabel() }}</h2>
        <button
          class="storyline__edit-btn"
          aria-label="Rename quest"
          title="Rename"
          @click="startEdit"
        >
          ✎
        </button>
      </template>
    </div>

    <p v-if="loading" class="storyline__msg">Loading…</p>
    <p v-else-if="photos.length === 0" class="storyline__msg">No photos.</p>

    <ul v-else class="storyline__list">
      <li
        v-for="(photo, i) in photos"
        :key="photo.id"
        class="storyline__item"
        :class="{ 'storyline__item--orphan': photo.is_orphan }"
      >
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
        <div class="storyline__info">
          <span class="storyline__date">{{ formatDate(photo.captured_at) }}</span>
          <div class="storyline__actions">
            <button
              class="storyline__action-btn storyline__action-btn--pin"
              :class="{
                'storyline__action-btn--active': placementStore.placingPhotoId === photo.id,
                'storyline__action-btn--placed': !photo.is_orphan,
              }"
              title="Place on map"
              @click="placementStore.startPlacing(photo.id)"
            >
              📍
            </button>
            <button
              class="storyline__action-btn storyline__action-btn--danger"
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

.storyline__header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.75rem 0.45rem;
  border-bottom: 1px solid #2a2a4e;
  flex-shrink: 0;
  min-height: 2.1rem;
}

.storyline__title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #ccc;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.storyline__edit-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0 2px;
  line-height: 1;
  flex-shrink: 0;
}

.storyline__edit-btn:hover {
  color: #aaa;
}

.storyline__name-input {
  flex: 1;
  background: #1e1e38;
  border: 1px solid #4a4a8e;
  border-radius: 3px;
  color: white;
  font-size: 0.8rem;
  padding: 2px 6px;
  outline: none;
  min-width: 0;
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
  border-left: 3px solid transparent;
}

.storyline__item--orphan {
  border-left-color: #f59e0b;
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

.storyline__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.storyline__date {
  font-size: 0.65rem;
  color: #999;
  line-height: 1.3;
  word-break: break-all;
}

.storyline__actions {
  display: flex;
  gap: 0.2rem;
}

.storyline__action-btn {
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 2px;
  border-radius: 3px;
  opacity: 0.5;
  line-height: 1;
  transition:
    opacity 0.15s,
    border-color 0.15s;
}

.storyline__action-btn:hover {
  opacity: 1;
  border-color: #4a4a8e;
  background: #2a2a4e;
}

.storyline__action-btn--pin {
  border-radius: 50%;
}

.storyline__action-btn--pin:hover {
  border-color: #c0392b;
  background: #2a1a1e;
}

.storyline__action-btn--pin.storyline__action-btn--placed {
  opacity: 1;
}

.storyline__action-btn--active {
  opacity: 1;
  background: #3b1a22;
  border-color: #c0392b;
}

.storyline__action-btn--danger {
  border-radius: 50%;
  color: #e06c75;
  font-size: 0.7rem;
  font-weight: 700;
}

.storyline__action-btn--danger:hover {
  background: #2a1a1e;
  border-color: #c0392b;
  color: #ff6b6b;
}
</style>

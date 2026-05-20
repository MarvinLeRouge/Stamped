<script setup lang="ts">
import { onMounted } from 'vue'

import { useQuestsStore } from '@/stores/quests'
import { useStatusStore } from '@/stores/status'

const store = useQuestsStore()
const statusStore = useStatusStore()

onMounted(() => {
  store.fetchQuests()
})

function select(id: number | null): void {
  store.selectQuest(store.selectedQuestId === id ? null : id)
}

function label(name: string | null, autoName: string): string {
  return name ?? autoName
}
</script>

<template>
  <aside class="quest-list">
    <h2 class="quest-list__title">Quests</h2>

    <p v-if="store.loading" class="quest-list__msg">Loading…</p>
    <p v-else-if="store.error" class="quest-list__msg quest-list__msg--error">
      {{ store.error }}
    </p>
    <p v-else-if="store.quests.length === 0" class="quest-list__msg">No quests yet.</p>

    <ul v-else class="quest-list__items">
      <li
        v-for="quest in store.quests"
        :key="quest.id"
        class="quest-list__item"
        :class="{ 'quest-list__item--active': store.selectedQuestId === quest.id }"
        @click="select(quest.id)"
      >
        <span class="quest-list__name">{{ label(quest.name, quest.auto_name) }}</span>
        <span class="quest-list__meta">
          {{ quest.photo_count }} photos
          <span v-if="quest.has_gpx" class="quest-list__gpx">GPX</span>
        </span>
      </li>
    </ul>

    <div
      v-if="statusStore.status && statusStore.status.unquested > 0"
      class="quest-list__unquested"
      :class="{ 'quest-list__unquested--active': store.showUnquested }"
      @click="store.toggleUnquested()"
    >
      <span class="quest-list__name">Sans quest</span>
      <span class="quest-list__meta">{{ statusStore.status.unquested }} photos</span>
    </div>

    <div
      class="quest-list__all"
      :class="{ 'quest-list__all--active': store.showAllPhotos }"
      @click="store.toggleAllPhotos()"
    >
      <span class="quest-list__name">Toutes les photos</span>
      <span v-if="statusStore.status" class="quest-list__meta">
        {{ statusStore.status.photos_total }} photos
      </span>
    </div>
  </aside>
</template>

<style scoped>
.quest-list {
  min-width: 180px;
  max-width: 280px;
  background: #1a1a2e;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.quest-list__title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #aaa;
  padding: 0.75rem 1rem 0.5rem;
  border-bottom: 1px solid #2a2a4e;
}

.quest-list__msg {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #888;
}

.quest-list__msg--error {
  color: #f87171;
}

.quest-list__items {
  list-style: none;
  overflow-y: auto;
  flex: 1;
}

.quest-list__item {
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #232340;
  transition: background 0.15s;
}

.quest-list__item:hover {
  background: #2a2a4e;
}

.quest-list__item--active {
  background: #3b3b6e;
}

.quest-list__name {
  display: block;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quest-list__meta {
  display: block;
  font-size: 0.8rem;
  color: #888;
  margin-top: 2px;
}

.quest-list__unquested {
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-top: 1px solid #2a2a4e;
  transition: background 0.15s;
  flex-shrink: 0;
}

.quest-list__unquested:hover {
  background: #2a2a4e;
}

.quest-list__unquested--active {
  background: #3b3b6e;
}

.quest-list__all {
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-top: 1px solid #2a2a4e;
  transition: background 0.15s;
  flex-shrink: 0;
}

.quest-list__all:hover {
  background: #2a2a4e;
}

.quest-list__all--active {
  background: #3b3b6e;
}

.quest-list__gpx {
  margin-left: 0.4rem;
  background: #4ade80;
  color: #000;
  border-radius: 2px;
  padding: 0 3px;
  font-size: 0.75rem;
  font-weight: 700;
}
</style>

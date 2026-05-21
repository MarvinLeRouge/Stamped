<script setup lang="ts">
import AllPhotosPanel from '@/components/AllPhotosPanel.vue'
import ElevationPanel from '@/components/ElevationPanel.vue'
import LayerSelector from '@/components/LayerSelector.vue'
import MapView from '@/components/MapView.vue'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import QuestList from '@/components/QuestList.vue'
import QuestStoryline from '@/components/QuestStoryline.vue'
import UnquestedPanel from '@/components/UnquestedPanel.vue'
import StatusDashboard from '@/components/StatusDashboard.vue'
import { useQuestsStore } from '@/stores/quests'
import { useElevationStore } from '@/stores/elevation'

const questsStore = useQuestsStore()
const elevationStore = useElevationStore()
</script>

<template>
  <div class="app">
    <header class="toolbar">
      <h1 class="logo">Stamped</h1>
      <StatusDashboard />
    </header>
    <div
      class="content"
      :class="{
        'content--with-storyline':
          questsStore.selectedQuestId !== null ||
          questsStore.showUnquested ||
          questsStore.showAllPhotos,
      }"
    >
      <QuestList />
      <QuestStoryline />
      <UnquestedPanel />
      <AllPhotosPanel />
      <main class="map-container">
        <div class="map-wrapper">
          <MapView />
          <LayerSelector />
          <button
            v-if="elevationStore.points.length > 0"
            class="elevation-toggle"
            :class="{ 'elevation-toggle--active': elevationStore.visible }"
            :title="elevationStore.visible ? 'Hide elevation' : 'Show elevation'"
            @click="elevationStore.toggle()"
          >
            ↑↓
          </button>
        </div>
        <ElevationPanel />
      </main>
    </div>
    <PhotoLightbox />
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body,
#app {
  height: 100%;
  width: 100%;
}
</style>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 1rem;
  background: #1a1a2e;
  color: white;
  flex-shrink: 0;
  z-index: 1000;
}

.logo {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.content {
  display: grid;
  grid-template-columns: minmax(180px, max-content) 1fr;
  flex: 1;
  overflow: hidden;
}

.content--with-storyline {
  grid-template-columns: minmax(180px, max-content) minmax(180px, max-content) 1fr;
}

.map-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.map-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

.elevation-toggle {
  position: absolute;
  bottom: 2rem;
  right: 4.5rem;
  z-index: 1000;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: all 0.15s;
}

.elevation-toggle:hover {
  background: #f0f0f0;
}

.elevation-toggle--active {
  background: #1a1a2e;
  border-color: #1a1a2e;
  color: white;
}
</style>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { useLightboxStore } from '@/stores/lightbox'

const store = useLightboxStore()

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') store.close()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div v-if="store.photoId !== null" class="lightbox" @click.self="store.close()">
      <div class="lightbox__box">
        <button class="lightbox__close" aria-label="Fermer" @click="store.close()">×</button>
        <img :src="`/api/photos/${store.photoId}/thumb`" class="lightbox__img" alt="photo" />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.lightbox__box {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.lightbox__img {
  display: block;
  max-width: 90vw;
  max-height: 85vh;
  border-radius: 4px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}

.lightbox__close {
  position: absolute;
  top: -2rem;
  right: 0;
  background: none;
  border: none;
  color: white;
  font-size: 1.8rem;
  line-height: 1;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  opacity: 0.8;
}

.lightbox__close:hover {
  opacity: 1;
}
</style>

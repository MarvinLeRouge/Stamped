<script setup lang="ts">
import { LAYERS, useLayerStore } from '@/stores/layer'

const layerStore = useLayerStore()
</script>

<template>
  <div class="layer-selector">
    <button
      v-for="layer in LAYERS"
      :key="layer.id"
      class="layer-selector__btn"
      :class="{ 'layer-selector__btn--active': layerStore.activeLayerId === layer.id }"
      :title="layer.label"
      @click="layerStore.setLayer(layer.id)"
    >
      {{ layer.label }}
    </button>
  </div>
</template>

<style scoped>
.layer-selector {
  position: absolute;
  bottom: 2rem;
  right: 0.75rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.layer-selector__btn {
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 8px;
  text-align: center;
  transition: all 0.15s;
  min-width: 52px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-selector__btn:hover {
  background: #f0f0f0;
  border-color: #999;
}

.layer-selector__btn--active {
  background: #1a1a2e;
  border-color: #1a1a2e;
  color: white;
}
</style>

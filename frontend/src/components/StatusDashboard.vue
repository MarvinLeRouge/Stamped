<script setup lang="ts">
import { onMounted } from 'vue'

import { useStatusStore } from '@/stores/status'

const store = useStatusStore()
onMounted(() => store.fetch())
</script>

<template>
  <div class="status-dashboard">
    <span v-if="store.loading" class="status-item">Loading…</span>
    <span v-else-if="store.error" class="status-item status-error">{{ store.error }}</span>
    <template v-else-if="store.status">
      <span class="status-item">{{ store.status.photos_total }} photos</span>
      <span class="status-item">{{ store.status.quests }} quests</span>
      <span v-if="store.status.orphans > 0" class="status-item status-warn">
        {{ store.status.orphans }} orphans
      </span>
    </template>
  </div>
</template>

<style scoped>
.status-dashboard {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
}

.status-item {
  opacity: 0.85;
}

.status-error {
  color: #f87171;
}

.status-warn {
  color: #fbbf24;
}
</style>

<script setup lang="ts">
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from './stores/game'

const router = useRouter()
const store = useGameStore()

// Watch for room/game state changes and navigate accordingly
watch(() => store.inRoom, (inRoom) => {
  if (inRoom && store.currentRoom?.state === 'playing') {
    router.push('/game')
  }
})

watch(() => store.currentRoom?.state, (state) => {
  if (state === 'playing') {
    router.push('/game')
  } else if (state === 'finished' || state === 'waiting') {
    router.push('/')
  }
})
</script>

<template>
  <router-view />
</template>

<style scoped>
</style>

<script setup lang="ts">
import { ref } from 'vue'
import { useGameStore } from '../stores/game'

const store = useGameStore()
const playerId = ref('')
const roomId = ref('')
const roomName = ref('')

const WS_URL = 'ws://localhost:8000/ws'

function connect() {
  if (!playerId.value) {
    alert('请输入玩家ID')
    return
  }
  store.connect(WS_URL)
  setTimeout(() => {
    store.login(playerId.value)
  }, 500)
}

function createRoom() {
  if (!roomName.value) {
    alert('请输入房间名')
    return
  }
  store.createRoom(roomName.value)
}

function joinRoom() {
  if (!roomId.value) {
    alert('请输入房间ID')
    return
  }
  store.joinRoom(roomId.value)
}
</script>

<template>
  <div class="lobby">
    <h1>🎮 王者之奕</h1>
    
    <div class="connection-status">
      <span :class="{ connected: store.connected }">
        {{ store.connected ? '✅ 已连接' : '❌ 未连接' }}
      </span>
    </div>

    <div v-if="!store.connected" class="login-section">
      <h2>连接服务器</h2>
      <input v-model="playerId" placeholder="输入玩家ID" />
      <button @click="connect">连接</button>
    </div>

    <div v-else class="room-section">
      <div v-if="!store.inRoom">
        <h2>创建房间</h2>
        <input v-model="roomName" placeholder="房间名称" />
        <button @click="createRoom">创建</button>

        <h2>加入房间</h2>
        <input v-model="roomId" placeholder="房间ID" />
        <button @click="joinRoom">加入</button>
      </div>

      <div v-else class="room-info">
        <h2>房间: {{ store.currentRoom?.name }}</h2>
        <p>状态: {{ store.currentRoom?.state }}</p>
        
        <div class="players">
          <h3>玩家列表</h3>
          <div v-for="player in store.currentRoom?.players" :key="player.id" class="player">
            <span>玩家 {{ player.slot }}: {{ player.nickname }}</span>
            <span :class="{ ready: player.ready }">
              {{ player.ready ? '✅ 已准备' : '⏳ 待准备' }}
            </span>
          </div>
        </div>

        <button v-if="store.currentRoom?.state === 'waiting'" @click="store.ready">准备</button>
        <button v-if="store.currentRoom?.state === 'waiting'" @click="store.cancelReady">取消准备</button>
        <button @click="store.leaveRoom">离开房间</button>
      </div>
    </div>

    <div v-if="store.error" class="error">
      {{ store.error }}
    </div>
  </div>
</template>

<style scoped>
.lobby {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.connection-status {
  margin: 20px 0;
  font-size: 18px;
}

.connected {
  color: green;
}

.login-section, .room-section {
  margin: 20px 0;
}

input {
  display: block;
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  font-size: 16px;
}

button {
  padding: 10px 20px;
  margin: 5px;
  font-size: 16px;
  cursor: pointer;
}

.players {
  margin: 20px 0;
}

.player {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid #ccc;
  margin: 5px 0;
}

.ready {
  color: green;
}

.error {
  color: red;
  padding: 10px;
  background: #fee;
  border-radius: 4px;
}
</style>

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface Player {
  id: number
  user_id: string
  nickname: string
  avatar?: string
  slot?: number
  ready?: boolean
  hp?: number
  gold?: number
  level?: number
}

export interface Hero {
  id: string
  name: string
  cost: number
  star: number
  rarity?: string
  race?: string
  class?: string
}

export interface HeroInstance extends Hero {
  instance_id: string
}

export interface Room {
  id: string
  name: string
  state: 'waiting' | 'playing' | 'finished'
  players: Player[]
  maxPlayers: number
}

export interface GameState {
  round: number
  phase: 'preparation' | 'battle' | 'finished'
  players: Player[]
  myHand: HeroInstance[]
  myBench: HeroInstance[]
  shop: Hero[]
  myGold: number
  myLevel: number
  myExp: number
}

export const useGameStore = defineStore('game', () => {
  // State
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const playerId = ref<string>('')
  const sessionId = ref<string>('')
  const currentRoom = ref<Room | null>(null)
  const gameState = ref<GameState | null>(null)
  const error = ref<string>('')
  const reconnecting = ref(false)

  // Queue for messages sent before connection
  const messageQueue = ref<any[]>([])

  // Computed
  const inRoom = computed(() => currentRoom.value !== null)
  const inGame = computed(() => gameState.value !== null && gameState.value.phase !== 'finished')

  // Actions
  function connect(url: string) {
    if (ws.value?.readyState === WebSocket.OPEN) return

    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      console.log('[WS] Connected')
      connected.value = true
      reconnecting.value = false
      
      // Send queued messages
      while (messageQueue.value.length > 0) {
        const msg = messageQueue.value.shift()
        send(msg)
      }
    }

    ws.value.onclose = (e) => {
      console.log('[WS] Disconnected', e.code, e.reason)
      connected.value = false
      
      if (reconnecting.value) {
        setTimeout(() => connect(url), 3000)
      }
    }

    ws.value.onerror = (e) => {
      console.error('[WS] Error', e)
      error.value = 'WebSocket connection error'
    }

    ws.value.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        handleMessage(msg)
      } catch (err) {
        console.error('[WS] Parse error', err)
      }
    }
  }

  function send(data: any) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      messageQueue.value.push(data)
    }
  }

  function handleMessage(msg: any) {
    console.log('[WS] Received:', msg.type)

    switch (msg.type) {
      case 'connected':
        playerId.value = msg.player_id
        sessionId.value = msg.session_id
        break

      case 'reconnected':
        playerId.value = msg.player_id
        if (msg.room_id) {
          currentRoom.value = { id: msg.room_id, name: '', state: 'waiting', players: [], maxPlayers: 8 }
        }
        if (msg.game_state) {
          gameState.value = msg.game_state
        }
        break

      case 'room_created':
      case 'room_joined':
        currentRoom.value = {
          id: msg.room_id,
          name: msg.room_state?.name || '',
          state: msg.room_state?.state || 'waiting',
          players: msg.room_state?.players || [],
          maxPlayers: 8
        }
        break

      case 'room_left':
        currentRoom.value = null
        gameState.value = null
        break

      case 'player_joined':
        if (currentRoom.value) {
          currentRoom.value.players.push(msg.player)
        }
        break

      case 'player_left':
        if (currentRoom.value) {
          currentRoom.value.players = currentRoom.value.players.filter(p => p.id !== msg.player_id)
        }
        break

      case 'player_ready_changed':
        if (currentRoom.value) {
          const player = currentRoom.value.players.find(p => p.id === msg.player_id)
          if (player) player.ready = msg.ready
        }
        break

      case 'game_start':
        if (currentRoom.value) {
          currentRoom.value.state = 'playing'
        }
        break

      case 'player_state_update':
        if (gameState.value) {
          const player = gameState.value.players.find(p => p.id === msg.player_id)
          if (player) {
            Object.assign(player, msg.state)
          }
        }
        break

      case 'shop_refreshed':
        if (gameState.value) {
          gameState.value.shop = msg.heroes
        }
        break

      case 'player_gold_update':
        if (gameState.value) {
          gameState.value.myGold = msg.gold
        }
        break

      case 'player_level_update':
        if (gameState.value) {
          gameState.value.myLevel = msg.level
        }
        break

      case 'round_start':
        if (gameState.value) {
          gameState.value.round = msg.round
        }
        break

      case 'preparation_start':
        if (gameState.value) {
          gameState.value.phase = 'preparation'
          if (msg.gold_earned) {
            gameState.value.myGold = msg.gold_earned.total
          }
        }
        break

      case 'battle_start':
        if (gameState.value) {
          gameState.value.phase = 'battle'
        }
        break

      case 'game_over':
        if (gameState.value) {
          gameState.value.phase = 'finished'
        }
        break

      case 'error':
        error.value = msg.message
        break
    }
  }

  function login(playerId: string, token: string = '') {
    send({
      type: 'connect',
      player_id: playerId,
      token: token,
      version: '1.0.0'
    })
  }

  function createRoom(name: string) {
    send({
      type: 'create_room',
      name: name,
      config: { mode: 'ranked' }
    })
  }

  function joinRoom(roomId: string) {
    send({
      type: 'join_room',
      room_id: roomId
    })
  }

  function leaveRoom() {
    send({ type: 'leave_room' })
  }

  function ready() {
    send({ type: 'ready' })
  }

  function cancelReady() {
    send({ type: 'cancel_ready' })
  }

  function refreshShop() {
    send({ type: 'shop_refresh' })
  }

  function buyHero(heroIndex: number) {
    send({
      type: 'shop_buy',
      hero_index: heroIndex
    })
  }

  function buyExp() {
    send({ type: 'buy_exp' })
  }

  function reconnect(playerId: string, sessionId: string) {
    reconnecting.value = true
    send({
      type: 'reconnect',
      player_id: playerId,
      session_id: sessionId
    })
  }

  function disconnect() {
    reconnecting.value = false
    if (ws.value) {
      send({ type: 'disconnect', reason: 'User left' })
      ws.value.close()
      ws.value = null
    }
    connected.value = false
    currentRoom.value = null
    gameState.value = null
  }

  return {
    // State
    ws,
    connected,
    playerId,
    sessionId,
    currentRoom,
    gameState,
    error,
    // Computed
    inRoom,
    inGame,
    // Actions
    connect,
    send,
    login,
    createRoom,
    joinRoom,
    leaveRoom,
    ready,
    cancelReady,
    refreshShop,
    buyHero,
    buyExp,
    reconnect,
    disconnect
  }
})

<script setup lang="ts">
import { useGameStore } from '../stores/game'

const store = useGameStore()

function getPhaseText(phase: string) {
  switch (phase) {
    case 'preparation': return '准备阶段'
    case 'battle': return '战斗阶段'
    case 'finished': return '游戏结束'
    default: return phase
  }
}
</script>

<template>
  <div class="game">
    <div class="header">
      <h1>🎮 王者之奕 - 游戏进行中</h1>
      <div class="game-info">
        <span>回合: {{ store.gameState?.round || 1 }}</span>
        <span>阶段: {{ getPhaseText(store.gameState?.phase || 'preparation') }}</span>
      </div>
    </div>

    <div class="stats-bar">
      <div class="stat">
        <span class="label">💰 金币</span>
        <span class="value">{{ store.gameState?.myGold || 0 }}</span>
      </div>
      <div class="stat">
        <span class="label">⭐ 等级</span>
        <span class="value">{{ store.gameState?.myLevel || 1 }}</span>
      </div>
      <div class="stat">
        <span class="label">📚 经验</span>
        <span class="value">{{ store.gameState?.myExp || 0 }}</span>
      </div>
    </div>

    <div class="game-area">
      <!-- 对手区域 -->
      <div class="opponents">
        <h3>对手</h3>
        <div class="opponent-list">
          <div 
            v-for="player in store.gameState?.players.filter(p => String(p.id) !== store.playerId)" 
            :key="player.id"
            class="opponent"
          >
            <span>{{ player.nickname }}</span>
            <span class="hp">❤️ {{ player.hp || 100 }}</span>
          </div>
        </div>
      </div>

      <!-- 棋盘区域 -->
      <div class="board">
        <h3>棋盘 (8x7)</h3>
        <div class="chess-board">
          <div 
            v-for="y in 7" 
            :key="y" 
            class="board-row"
          >
            <div 
              v-for="x in 8" 
              :key="`${x}-${y}`" 
              class="board-cell"
            >
              <span class="cell-coord">{{ x }},{{ y }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 玩家状态 -->
      <div class="player-info">
        <h3>你的状态</h3>
        <div class="my-stats">
          <div>玩家ID: {{ store.playerId }}</div>
          <div>金币: {{ store.gameState?.myGold || 0 }}</div>
          <div>等级: {{ store.gameState?.myLevel || 1 }}</div>
        </div>
      </div>
    </div>

    <!-- 商店 -->
    <div v-if="store.gameState?.phase === 'preparation'" class="shop">
      <h3>商店</h3>
      <div class="shop-heroes">
        <div 
          v-for="(hero, index) in store.gameState?.shop" 
          :key="index"
          class="shop-hero"
          @click="store.buyHero(index)"
        >
          <div class="hero-cost">{{ hero.cost }} 💰</div>
          <div class="hero-name">{{ hero.name }}</div>
          <div class="hero-stars">{{ '★'.repeat(hero.star) }}</div>
        </div>
      </div>
      <button @click="store.refreshShop">🔄 刷新 (2金币)</button>
      <button @click="store.buyExp">📚 升级 (4金币)</button>
    </div>

    <!-- 备战席 -->
    <div class="bench">
      <h3>备战席</h3>
      <div class="bench-heroes">
        <div 
          v-for="hero in store.gameState?.myBench" 
          :key="hero.instance_id"
          class="bench-hero"
        >
          <div class="hero-name">{{ hero.name }}</div>
          <div class="hero-stars">{{ '★'.repeat(hero.star) }}</div>
        </div>
        <div v-if="!store.gameState?.myBench?.length" class="empty-bench">
          暂无英雄
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="store.leaveRoom">离开游戏</button>
    </div>
  </div>
</template>

<style scoped>
.game {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.game-info {
  display: flex;
  gap: 20px;
  font-size: 18px;
}

.stats-bar {
  display: flex;
  justify-content: center;
  gap: 40px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.stat {
  text-align: center;
}

.stat .label {
  display: block;
  font-size: 14px;
  color: #666;
}

.stat .value {
  font-size: 24px;
  font-weight: bold;
}

.game-area {
  display: grid;
  grid-template-columns: 200px 1fr 200px;
  gap: 20px;
  margin-bottom: 20px;
}

.opponents h3, .player-info h3, .shop h3, .bench h3 {
  margin-bottom: 10px;
}

.opponent {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin: 5px 0;
}

.chess-board {
  display: flex;
  flex-direction: column;
  border: 2px solid #333;
}

.board-row {
  display: flex;
}

.board-cell {
  width: 60px;
  height: 60px;
  border: 1px solid #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.board-cell:nth-child(odd) {
  background: #f5f5f5;
}

.cell-coord {
  font-size: 10px;
  color: #999;
}

.shop {
  padding: 20px;
  background: #fff8e0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.shop-heroes {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.shop-hero {
  width: 100px;
  height: 120px;
  background: white;
  border: 2px solid #ffd700;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.shop-hero:hover {
  transform: scale(1.05);
}

.hero-cost {
  font-weight: bold;
  color: #ff9800;
}

.hero-name {
  font-size: 14px;
  margin: 5px 0;
}

.hero-stars {
  color: #ffd700;
}

.bench {
  padding: 15px;
  background: #f0f0f0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.bench-heroes {
  display: flex;
  gap: 10px;
  min-height: 80px;
}

.bench-hero {
  width: 80px;
  height: 80px;
  background: white;
  border: 2px solid #4caf50;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  cursor: pointer;
}

.empty-bench {
  color: #999;
  padding: 20px;
}

.actions {
  text-align: center;
}

.actions button {
  padding: 12px 30px;
  font-size: 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.actions button:hover {
  background: #d32f2f;
}
</style>

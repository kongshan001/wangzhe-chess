# 王者之奕 - 内容更新计划

## 一、未来英雄设计方向

### 1.1 第一阶段：羁绊补充（v1.1）

#### 1.1.1 机关羁绊补充

**墨子 - 2费**
```json
{
  "name": "墨子",
  "title": "和平守望",
  "cost": 2,
  "origins": ["Machine", "Jixia"],
  "classes": ["Tank", "Mage"],
  "stats": {
    "hp": 750,
    "attack": 50,
    "armor": 55,
    "magic_resist": 50,
    "attack_speed": 0.6,
    "range": 3
  },
  "skill": {
    "name": "墨守成规",
    "mana_cost": 75,
    "initial_mana": 25,
    "description": "墨子展开能量护盾，为周围友军提供护盾并反弹伤害",
    "effects": [
      {"type": "ally_shield", "value": 200, "scaling": "ap", "radius": 2},
      {"type": "thorns", "value": 25, "duration": 4, "radius": 2}
    ]
  }
}
```

**盾山 - 3费**
```json
{
  "name": "盾山",
  "title": "无尽之盾",
  "cost": 3,
  "origins": ["Machine", "Guardians"],
  "classes": ["Tank", "Support"],
  "stats": {
    "hp": 950,
    "attack": 55,
    "armor": 68,
    "magic_resist": 52,
    "attack_speed": 0.55,
    "range": 1
  },
  "skill": {
    "name": "不动如山",
    "mana_cost": 80,
    "initial_mana": 30,
    "description": "盾山举起盾牌，格挡前方所有飞行物并为身后友军提供护盾",
    "effects": [
      {"type": "windwall", "duration": 4},
      {"type": "ally_shield", "value": 20, "scaling": "max_hp", "target": "behind", "duration": 4}
    ]
  }
}
```

#### 1.1.2 西域羁绊补充

**不知火舞 - 3费**
```json
{
  "name": "不知火舞",
  "title": "明媚烈焰",
  "cost": 3,
  "origins": ["Western", "Beauty"],
  "classes": ["Assassin", "Mage"],
  "stats": {
    "hp": 600,
    "attack": 75,
    "armor": 35,
    "magic_resist": 50,
    "attack_speed": 0.75,
    "range": 1
  },
  "skill": {
    "name": "必杀·忍蜂",
    "mana_cost": 85,
    "initial_mana": 35,
    "description": "不知火舞向前冲刺，对路径上敌人造成伤害并击退",
    "effects": [
      {"type": "line_damage", "damage_type": "magic", "value": 350, "scaling": "ap"},
      {"type": "knockback", "distance": 2}
    ]
  }
}
```

**宫本武藏 - 4费**
```json
{
  "name": "宫本武藏",
  "title": "剑圣",
  "cost": 4,
  "origins": ["Western", "Human"],
  "classes": ["Assassin", "Warrior"],
  "stats": {
    "hp": 680,
    "attack": 90,
    "armor": 42,
    "magic_resist": 40,
    "attack_speed": 0.8,
    "range": 1
  },
  "skill": {
    "name": "二天一流",
    "mana_cost": 100,
    "initial_mana": 40,
    "description": "宫本武藏锁定一名敌人发起斩击，造成伤害并使其减速，同时进入无敌状态",
    "effects": [
      {"type": "targeted_damage", "damage_type": "physical", "value": 450, "scaling": "attack", "target": "lowest_hp"},
      {"type": "slow", "value": 60, "duration": 2},
      {"type": "untargetable", "duration": 1}
    ]
  }
}
```

#### 1.1.3 长城守卫军补充

**百里守约 - 3费**
```json
{
  "name": "百里守约",
  "title": "静谧之眼",
  "cost": 3,
  "origins": ["Guardians", "Human"],
  "classes": ["Marksman", "Assassin"],
  "stats": {
    "hp": 550,
    "attack": 80,
    "armor": 30,
    "magic_resist": 35,
    "attack_speed": 0.7,
    "range": 5
  },
  "skill": {
    "name": "狂风之息",
    "mana_cost": 90,
    "initial_mana": 30,
    "description": "百里守约瞄准射击，对最远敌人造成巨额物理伤害",
    "effects": [
      {"type": "snipe_damage", "damage_type": "physical", "value": 500, "scaling": "attack", "target": "furthest"}
    ]
  }
}
```

**苏烈 - 4费**
```json
{
  "name": "苏烈",
  "title": "不屈铁壁",
  "cost": 4,
  "origins": ["Guardians", "Human"],
  "classes": ["Tank", "Warrior"],
  "stats": {
    "hp": 950,
    "attack": 70,
    "armor": 65,
    "magic_resist": 50,
    "attack_speed": 0.6,
    "range": 1
  },
  "skill": {
    "name": "豪烈万军",
    "mana_cost": 100,
    "initial_mana": 40,
    "description": "苏烈蓄力后砸向地面，造成AOE伤害并击飞，同时获得复活buff",
    "effects": [
      {"type": "aoe_damage", "damage_type": "physical", "value": 380, "scaling": "attack", "radius": 2.5},
      {"type": "knockup", "duration": 1.5, "radius": 2.5},
      {"type": "revive", "hp_percent": 30, "cooldown": 1}
    ]
  }
}
```

### 1.2 第二阶段：辅助补充（v1.2）

#### 1.2.1 辅助职业补充

**大乔 - 3费**
```json
{
  "name": "大乔",
  "title": "伊人如梦",
  "cost": 3,
  "origins": ["ThreeKingdoms", "Beauty"],
  "classes": ["Support"],
  "stats": {
    "hp": 620,
    "attack": 45,
    "armor": 38,
    "magic_resist": 55,
    "attack_speed": 0.65,
    "range": 3
  },
  "skill": {
    "name": "漩涡之门",
    "mana_cost": 90,
    "initial_mana": 30,
    "description": "大乔召唤传送门，将血量最低友军传送回安全位置并治疗",
    "effects": [
      {"type": "reposition", "target": "lowest_hp_ally", "position": "safest"},
      {"type": "heal", "value": 35, "scaling": "max_hp", "target": "repositioned"}
    ]
  }
}
```

**孙膑 - 4费**
```json
{
  "name": "孙膑",
  "title": "时光之神",
  "cost": 4,
  "origins": ["ThreeKingdoms", "Jixia"],
  "classes": ["Support"],
  "stats": {
    "hp": 650,
    "attack": 48,
    "armor": 40,
    "magic_resist": 60,
    "attack_speed": 0.65,
    "range": 3
  },
  "skill": {
    "name": "时光流逝",
    "mana_cost": 95,
    "initial_mana": 40,
    "description": "孙膑扭曲时空，使范围内敌人减速并延长其技能冷却，同时加速友军",
    "effects": [
      {"type": "slow", "value": 50, "duration": 3, "radius": 3},
      {"type": "debuff", "attribute": "cooldown", "value": 50, "duration": 3, "radius": 3},
      {"type": "buff", "attribute": "attack_speed", "value": 30, "duration": 3, "target": "allies", "radius": 3}
    ]
  }
}
```

### 1.3 第三阶段：新羁绊（v1.5）

#### 1.3.1 暗影羁绊

**兰陵王 - 3费**
```json
{
  "name": "兰陵王",
  "title": "影刃",
  "cost": 3,
  "origins": ["Shadow", "Human"],
  "classes": ["Assassin"],
  "stats": {
    "hp": 620,
    "attack": 78,
    "armor": 38,
    "magic_resist": 38,
    "attack_speed": 0.8,
    "range": 1
  },
  "skill": {
    "name": "秘技·影袭",
    "mana_cost": 80,
    "initial_mana": 30,
    "description": "兰陵王进入隐身状态，下次攻击造成额外伤害并沉默",
    "effects": [
      {"type": "stealth", "duration": 3},
      {"type": "bonus_damage", "value": 200, "scaling": "attack", "trigger": "on_attack"},
      {"type": "silence", "duration": 2, "trigger": "on_attack"}
    ]
  }
}
```

**司马懿 - 4费**
```json
{
  "name": "司马懿",
  "title": "寂灭之心",
  "cost": 4,
  "origins": ["Shadow", "Demon"],
  "classes": ["Assassin", "Mage"],
  "stats": {
    "hp": 600,
    "attack": 70,
    "armor": 35,
    "magic_resist": 55,
    "attack_speed": 0.75,
    "range": 1
  },
  "skill": {
    "name": "死神降临",
    "mana_cost": 100,
    "initial_mana": 40,
    "description": "司马懿瞬移到目标身后，造成伤害并沉默，击杀后刷新冷却",
    "effects": [
      {"type": "teleport", "target": "lowest_hp_enemy"},
      {"type": "damage", "damage_type": "magic", "value": 400, "scaling": "ap"},
      {"type": "silence", "duration": 2},
      {"type": "reset_cooldown", "condition": "kill"}
    ]
  }
}
```

---

## 二、新羁绊规划

### 2.1 暗影羁绊

| 层级 | 英雄数 | 效果 |
|------|--------|------|
| 2 | 2 | 暗影英雄开局隐身2秒，首次攻击必定暴击 |
| 4 | 4 | 暗影英雄开局隐身4秒，暴击伤害+50% |
| 6 | 6 | 暗影英雄开局隐身6秒，暴击伤害+100%，击杀后再次隐身 |

**候选英雄**：
- 兰陵王（3费）
- 司马懿（4费）
- 新增：阿轲（2费）、娜可露露（3费）、马超（4费）、云中君（5费）

### 2.2 元素羁绊

| 层级 | 英雄数 | 效果 |
|------|--------|------|
| 2 | 2 | 元素英雄技能附带元素效果（冰/火/雷） |
| 4 | 4 | 元素英雄技能伤害+30%，元素效果强化 |
| 6 | 6 | 元素英雄技能伤害+50%，双重元素效果 |

**候选英雄**：
- 王昭君（3费，冰）
- 周瑜（4费，火）
- 女娲（5费，光）
- 新增：奕星（2费）、沈梦溪（3费）、甄姬（已有，冰）

### 2.3 召唤羁绊

| 层级 | 英雄数 | 效果 |
|------|--------|------|
| 2 | 2 | 召唤物数量+1 |
| 4 | 4 | 召唤物数量+2，召唤物继承50%属性 |
| 6 | 6 | 召唤物数量+3，召唤物继承75%属性，死亡时自爆 |

**候选英雄**：
- 米莱狄（3费）
- 娜可露露（4费）
- 新增：梦奇（2费）、太乙真人（3费）、东皇太一（4费）、元歌（5费）

---

## 三、赛季更新策略

### 3.1 赛季节奏

| 赛季 | 时长 | 核心内容 |
|------|------|----------|
| S1 | 3个月 | 基础版本，30英雄 |
| S2 | 3个月 | 新增10英雄，2新羁绊 |
| S3 | 3个月 | 新增8英雄，装备系统 |
| S4 | 3个月 | 新增8英雄，天赋系统 |

### 3.2 S1赛季规划（当前）

**目标**：验证基础玩法，收集数据

| 阶段 | 时间 | 内容 |
|------|------|------|
| 第一周 | Week 1 | 内测，收集反馈 |
| 第二周 | Week 2 | 修复Bug，小幅平衡 |
| 第三周 | Week 3 | 新增6英雄（羁绊补充） |
| 第四周 | Week 4 | 数据分析，大范围平衡 |
| 第五-八周 | Week 5-8 | 稳定运营，准备S2 |
| 第九-十二周 | Week 9-12 | S1收尾，S2预热 |

### 3.3 S2赛季规划

**主题**：暗影降临

**新增内容**：
1. **新羁绊**：暗影（6英雄）
2. **新羁绊**：元素（6英雄）
3. **新机制**：装备强化系统
4. **新模式**：双人组队模式

**英雄计划**：
- 兰陵王（3费，暗影/刺客）
- 司马懿（4费，暗影/法刺）
- 阿轲（2费，暗影/刺客）
- 娜可露露（3费，暗影/刺客）
- 马超（4费，暗影/战士）
- 云中君（5费，暗影/刺客）

### 3.4 S3赛季规划

**主题**：召唤师峡谷

**新增内容**：
1. **新羁绊**：召唤（6英雄）
2. **新系统**：装备合成
3. **新机制**：野怪装备掉落
4. **新模式**：快速模式（15分钟）

**英雄计划**：
- 米莱狄（3费，召唤/法师）
- 元歌（5费，召唤/刺客）
- 太乙真人（3费，召唤/辅助）
- 梦奇（2费，召唤/坦克）
- 东皇太一（4费，召唤/坦克）
- 鬼谷子（已有，纳入召唤）

### 3.5 S4赛季规划

**主题**：天赋觉醒

**新增内容**：
1. **新系统**：天赋选择（每3回合选1）
2. **新羁绊**：觉醒（强化版羁绊）
3. **新机制**：英雄专属天赋
4. **新模式**：无限火力（随机英雄）

---

## 四、运营节奏

### 4.1 更新频率

| 类型 | 频率 | 内容 |
|------|------|------|
| 热更新 | 每日 | Bug修复，紧急平衡 |
| 小更新 | 每周 | 数值微调，活动更新 |
| 中更新 | 每月 | 新英雄，新功能 |
| 大更新 | 每季 | 新羁绊，新系统，新模式 |

### 4.2 活动规划

**周常活动**：
- 周末双倍金币
- 每日任务奖励
- 阵容挑战（使用指定阵容获胜）

**月常活动**：
- 限时模式
- 皮肤抽奖
- 累计登录奖励

**赛季活动**：
- 赛季通行证
- 段位奖励
- 赛季专属皮肤

### 4.3 社区运营

**内容输出**：
- 每周阵容推荐
- 英雄攻略视频
- 开发者日志

**互动活动**：
- 玩家创意征集
- 阵容搭配大赛
- 直播活动

---

## 五、数据监控

### 5.1 核心指标

| 指标 | 目标值 | 预警值 | 处理方式 |
|------|--------|--------|----------|
| DAU | >100万 | <50万 | 运营活动刺激 |
| 次日留存 | >40% | <30% | 新手引导优化 |
| 7日留存 | >20% | <15% | 新手礼包优化 |
| 平均时长 | >30分钟 | <20分钟 | 玩法节奏调整 |
| 付费率 | >5% | <3% | 商业化优化 |

### 5.2 平衡指标

| 指标 | 目标值 | 预警值 | 处理方式 |
|------|--------|--------|----------|
| 英雄出场率 | 10%-30% | <5%或>40% | 数值调整 |
| 阵容多样性 | >8种 | <5种 | 羁绊调整 |
| 平均排名分布 | 3.5-4.5 | <3.0或>5.0 | 英雄调整 |
| 前4率 | 45%-55% | <40%或>60% | 大范围调整 |

---

## 六、总结

### 6.1 短期目标（1个月内）
- 补充6个英雄，解决羁绊英雄不足问题
- 调整过强羁绊（人族、三国）
- 修复已知Bug

### 6.2 中期目标（3个月内）
- 新增2个羁绊
- 完善装备系统
- 优化新手体验

### 6.3 长期目标（6个月以上）
- 英雄数量达到50+
- 建立完整的赛季体系
- 形成稳定的运营节奏

---

*文档版本：v1.0*
*规划日期：2026年2月21日*
*下次更新：S1赛季结束时*

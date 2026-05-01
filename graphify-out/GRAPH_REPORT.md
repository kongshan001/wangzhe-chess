# Graph Report - wangzhe-chess  (2026-04-28)

## Corpus Check
- 193 files · ~209,563 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6207 nodes · 19918 edges · 43 communities detected
- Extraction: 39% EXTRACTED · 61% INFERRED · 0% AMBIGUOUS · INFERRED: 12070 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]

## God Nodes (most connected - your core abstractions)
1. `BaseMessage` - 308 edges
2. `Hero` - 224 edges
3. `Session` - 220 edges
4. `Base` - 192 edges
5. `IdMixin` - 177 edges
6. `王者之奕 - 协议模块  本模块提供 WebSocket 通信的协议定义和编解码功能。  主要导出： - 消息类型（MessageType 枚举和具体消息类）` - 176 edges
7. `TimestampMixin` - 167 edges
8. `HeroTemplate` - 137 edges
9. `SynergyType` - 108 edges
10. `ErrorMessage` - 108 edges

## Surprising Connections (you probably didn't know these)
- `synergy_manager()` --calls--> `SynergyManager`  [INFERRED]
  tests/conftest.py → src/server/game/synergy.py
- `economy_manager()` --calls--> `EconomyManager`  [INFERRED]
  tests/conftest.py → src/server/game/economy.py
- `manager()` --calls--> `SeasonManager`  [INFERRED]
  tests/test_season.py → src/server/match/rating.py
- `friendship_manager()` --calls--> `FriendshipManager`  [INFERRED]
  tests/integration/conftest.py → src/server/friendship/manager.py
- `crafting_manager()` --calls--> `CraftingManager`  [INFERRED]
  tests/integration/conftest.py → src/server/game/crafting/manager.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (607): AICoachWSHandler, 处理分析阵容请求          Args:             session: WebSocket 会话             message: 分, 处理获取阵容推荐请求          Args:             session: WebSocket 会话             message:, 处理获取对局历史请求          Args:             session: WebSocket 会话             message:, 处理获取装备建议请求          Args:             session: WebSocket 会话             message:, 处理获取站位建议请求          Args:             session: WebSocket 会话             message:, 处理获取回合策略请求          Args:             session: WebSocket 会话             message:, 处理获取胜率预测请求          Args:             session: WebSocket 会话             message: (+599 more)

### Community 1 - "Community 1"
Cohesion: 0.01
Nodes (203): 王者之奕 - 战斗模块  本模块包含战斗相关的子模块： - simulator: 确定性战斗模拟器, attack_speed(), BattleSimulator, BattleUnit, create_test_board(), create_test_hero(), DeterministicRNG, hp_percent() (+195 more)

### Community 2 - "Community 2"
Cohesion: 0.01
Nodes (279): ErrorResponse, get_player(), get_player_inventory(), get_player_rank(), get_player_stats(), InventoryItemResponse, PlayerDetailResponse, PlayerListItem (+271 more)

### Community 3 - "Community 3"
Cohesion: 0.02
Nodes (152): 王者之奕 - 表情系统模块  本模块提供游戏中表情发送和管理功能： - 表情分类和列表 - 表情发送/接收 - 表情解锁 - 快捷键设置 - 表情历史记录, EmoteManager, get_emote_manager(), 王者之奕 - 表情系统管理器  本模块提供表情系统的管理功能： - EmoteManager: 表情管理器类 - 表情列表获取 - 表情发送/接收 - 表情解锁, 获取所有表情列表          Returns:             表情列表（按排序顺序）, 获取指定分类的表情          Args:             category: 表情分类          Returns:, 获取单个表情          Args:             emote_id: 表情ID          Returns:             表, 获取表情列表数据（用于发送给客户端）          Returns:             表情数据列表 (+144 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (146): add_request_id(), add_service_info(), add_timestamp(), clear_request_id(), ColoredFormatter, drop_color_message_key(), extract_from_record(), get_logger() (+138 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (105): 王者之奕 - 签到系统模块  本模块提供签到系统的核心功能： - 签到数据模型 - 签到管理器 - 奖励配置加载, CheckinManager, get_checkin_manager(), 王者之奕 - 签到管理器  本模块提供签到系统的管理功能： - CheckinManager: 签到管理器类 - 每日签到处理 - 签到奖励发放 - 连续签到计, 从配置文件加载签到奖励          Args:             config_path: 配置文件路径, 保存签到配置到文件          Args:             config_path: 配置文件路径, 获取或创建玩家连续签到数据          Args:             player_id: 玩家ID          Returns:, 获取玩家签到记录          Args:             player_id: 玩家ID             limit: 返回数量限制 (+97 more)

### Community 6 - "Community 6"
Cohesion: 0.03
Nodes (139): manager(), 王者之奕 - AI教练系统 WebSocket 处理器  本模块提供AI教练系统相关的 WebSocket 消息处理： - 获取教练建议 - 分析阵容 - 获取, BaseMessage, manager(), 王者之奕 - 交易系统测试  本模块测试交易系统的功能： - 交易请求创建 - 交易接受/拒绝 - 交易取消 - 交易确认 - 交易执行 - 交易税计算 - 每, TestTaxCalculation, TestTradeHistory, TestTradeItem (+131 more)

### Community 7 - "Community 7"
Cohesion: 0.02
Nodes (95): is_empty(), TestCheckinSerialization, TestRoomSerialization, 王者之奕 - 新手引导与游戏流程集成测试  测试新手引导与游戏流程的跨模块交互： - 引导步骤与游戏操作关联 - 引导完成触发奖励 - 前置引导检查 - 引导进, TestTutorialAndGameFlowIntegration, TestTutorialIntegration, TestTutorialPrerequisitesIntegration, TestTutorialProgressIntegration (+87 more)

### Community 8 - "Community 8"
Cohesion: 0.02
Nodes (120): get_display_name(), Enum, Rarity, SpecialEffectType, IntEnum, compare_elo(), EloBasedRatingUpdater, EloCalculator (+112 more)

### Community 9 - "Community 9"
Cohesion: 0.02
Nodes (98): 王者之奕 - 自定义房间模块  本模块实现自定义房间系统（需求 #16）：  功能: - 创建自定义房间（设置房间名、密码、人数、规则） - 特殊规则支持（随机, CustomRoomFilter, CustomRoomManager, get_instance(), 王者之奕 - 自定义房间管理器  本模块实现自定义房间系统的核心管理逻辑： - CustomRoomManager: 自定义房间管理器（单例） - 房间创建/销, 重置管理器（仅用于测试）          警告：此操作会清除所有房间数据！, 创建自定义房间          Args:             host_id: 房主ID             host_name: 房主昵称, 销毁房间          Args:             room_id: 房间ID          Returns:             是否成功 (+90 more)

### Community 10 - "Community 10"
Cohesion: 0.04
Nodes (112): 王者之奕 - 英雄碎片系统  本模块提供英雄碎片系统的完整功能： - 碎片获取和管理 - 英雄合成（100碎片=1星，3个1星+50碎片=2星等） - 英雄分解, get_hero_shard_manager(), HeroShardManager, 王者之奕 - 英雄碎片管理器  本模块提供英雄碎片系统的管理功能： - HeroShardManager: 碎片管理器类 - 碎片数量管理 - 英雄合成逻辑 -, 获取玩家碎片背包信息          Args:             player_id: 玩家ID          Returns:, 增加碎片          Args:             player_id: 玩家ID             hero_id: 英雄ID, 批量增加碎片          Args:             player_id: 玩家ID             shards_data: 碎片数据列, 获取合成配置          Args:             target_star: 目标星级          Returns: (+104 more)

### Community 11 - "Community 11"
Cohesion: 0.03
Nodes (92): Exception, float, int, duration_seconds(), session_duration(), ReplayDB, 王者之奕 - 回放系统模块  本模块提供回放系统的核心功能： - 保存对局回放 - 播放回放（支持倍速、跳转） - 分享和导入回放  主要组件： - Repla, get_replay_manager() (+84 more)

### Community 12 - "Community 12"
Cohesion: 0.04
Nodes (114): BuySkinMessage, EquipSkinMessage, GetHeroSkinsMessage, GetOwnedSkinsMessage, GetSkinsMessage, HeroSkinsListMessage, OwnedSkinsListMessage, PlayerSkinData (+106 more)

### Community 13 - "Community 13"
Cohesion: 0.02
Nodes (67): reset(), create_economy_manager(), EconomyManager, EconomyState, from_dict(), get_income_table(), get_level_table(), get_streak_bonus_table() (+59 more)

### Community 14 - "Community 14"
Cohesion: 0.04
Nodes (67): get_description(), 王者之奕 - 每日任务系统  本模块提供每日任务系统功能： - 每日任务刷新 - 任务进度追踪 - 任务奖励领取 - 金币刷新任务, DailyTaskManager, get_daily_task_manager(), 王者之奕 - 每日任务管理器  本模块提供每日任务系统的管理功能： - DailyTaskManager: 每日任务管理器类 - 每日任务刷新（0点） - 检查, 从配置文件加载任务模板          Args:             config_path: 配置文件路径, 保存任务配置到文件          Args:             config_path: 配置文件路径（默认使用初始化时的路径）, 根据权重随机选择任务模板          Args:             count: 需要选择的数量             exclude_ids: (+59 more)

### Community 15 - "Community 15"
Cohesion: 0.03
Nodes (65): checkin_manager(), crafting_manager(), custom_room_manager(), daily_task_manager(), friendship_manager(), leaderboard_manager(), tutorial_manager(), leaderboard_manager() (+57 more)

### Community 16 - "Community 16"
Cohesion: 0.03
Nodes (67): 王者之奕 - 阵容预设与游戏流程集成测试  测试阵容预设与游戏流程的跨模块交互： - 预设保存与数据库持久化 - 预设应用到游戏对局 - 预设版本管理 - 预设, sample_preset(), sample_slots(), sample_synergies(), test_delete_preset(), test_delete_preset_not_found(), test_get_player_presets(), test_save_preset_exceeds_limit() (+59 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (71): 王者之奕 - 道具系统模块  本模块提供道具系统的核心功能： - 道具数据模型 - 道具管理器 - 道具效果计算, ConsumableManager, get_consumable_manager(), 王者之奕 - 道具管理器  本模块提供道具系统的管理功能： - ConsumableManager: 道具管理器类 - 道具配置加载 - 道具获取、使用、添加, 获取道具配置          Args:             consumable_id: 道具ID          Returns:, 获取所有道具          Returns:             道具列表, 获取指定类型的道具          Args:             ctype: 道具类型          Returns:             道, 获取指定稀有度的道具          Args:             rarity: 道具稀有度          Returns: (+63 more)

### Community 18 - "Community 18"
Cohesion: 0.04
Nodes (55): 王者之奕 - AI教练系统  本模块提供AI教练功能，帮助玩家提升游戏水平： - 阵容分析与建议 - 装备合成建议 - 站位优化 - 回合策略 - 胜率预测 -, AICoachManager, get_ai_coach_manager(), 王者之奕 - AI教练系统管理器  本模块提供AI教练系统的核心管理功能： - AICoachManager: AI教练管理器类 - 分析当前阵容 - 推荐阵容, 获取站位建议          Args:             player_id: 玩家ID             board: 当前棋盘状态, 获取回合策略          Args:             player_id: 玩家ID             round_num: 当前回合, 预测胜率          Args:             player_id: 玩家ID             game_state: 游戏状态, 获取对局历史          Args:             player_id: 玩家ID             limit: 返回数量限制 (+47 more)

### Community 19 - "Community 19"
Cohesion: 0.02
Nodes (59): get_random_event_manager(), GameRoom, PlayerInRoom, PlayerState, 王者之奕 - 游戏房间模块  本模块实现游戏房间的核心逻辑： - GameRoom: 8人游戏房间管理 - 游戏状态机（等待→准备→战斗→结算） - 回合控制, 强制结束游戏          房主或管理员可以调用, 获取房间完整状态（用于同步）          Returns:             包含房间所有状态的字典, 获取指定玩家的详细状态          Args:             player_id: 玩家ID          Returns: (+51 more)

### Community 20 - "Community 20"
Cohesion: 0.04
Nodes (61): is_full(), 王者之奕 - 观战系统  本模块提供观战功能的完整实现： - 观战会话管理 - 延迟同步机制（30秒防作弊） - 弹幕/聊天系统 - 可观战对局列表  主要组件, get_spectator_manager(), 王者之奕 - 观战系统管理器  本模块提供观战系统的核心管理功能： - SpectatorManager: 观战管理器类 - 创建/销毁观战会话 - 管理观众加, 创建可观战对局          Args:             game_id: 对局ID             visibility: 可见性, 移除可观战对局          Args:             game_id: 对局ID          Returns:             被, 获取可观战对局          Args:             game_id: 对局ID          Returns:             观, 检查对局是否可观战          Args:             game_id: 对局ID          Returns: (+53 more)

### Community 21 - "Community 21"
Cohesion: 0.04
Nodes (45): 王者之奕 - 装备合成系统  本模块提供装备合成功能： - 合成配方管理 - 材料消耗 - 金币扣除 - 合成历史记录  使用示例:     from serv, CraftingManager, create_crafting_manager(), from_dict(), PlayerInventory, 查找匹配所提供装备的配方          Args:             equipment_ids: 装备ID列表          Returns:, 查找使用指定装备的所有配方          Args:             equipment_id: 装备ID          Returns:, 检查是否可以执行合成          Args:             recipe: 合成配方             inventory: 玩家背包 (+37 more)

### Community 22 - "Community 22"
Cohesion: 0.06
Nodes (55): 王者之奕 - 随机事件系统  本模块实现对局中的随机事件系统： - 随机触发特殊事件 - 事件效果执行 - 事件历史记录  事件类型： - 金币雨：所有玩家获得, ActiveEvent, create_random_event_manager(), RandomEventManager, 王者之奕 - 随机事件管理器  本模块实现随机事件的核心管理逻辑： - 检查事件触发 - 执行事件效果 - 管理事件配置 - 记录事件历史, 检查是否有免费刷新          Args:             room_id: 房间ID             player_id: 玩家ID, 获取羁绊加成百分比          Args:             room_id: 房间ID             player_id: 玩家ID, 获取掉落率加成          Args:             room_id: 房间ID             player_id: 玩家ID (+47 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (51): 王者之奕 - 成就系统  本模块提供成就系统功能： - Achievement: 成就数据类 - AchievementRequirement: 成就需求 -, AchievementManager, get_achievement_manager(), 王者之奕 - 成就管理器  本模块提供成就系统的管理功能： - AchievementManager: 成就管理器类 - 检查成就进度 - 完成成就奖励 - 加, 从配置文件加载成就          Args:             config_path: 配置文件路径, 保存成就配置到文件          Args:             config_path: 配置文件路径（默认使用初始化时的路径）, 成就管理器      负责管理所有成就相关的操作：     - 成就配置加载     - 成就进度检查     - 成就完成奖励发放     - 成就统计查询, 获取指定成就          Args:             achievement_id: 成就ID          Returns: (+43 more)

### Community 24 - "Community 24"
Cohesion: 0.05
Nodes (43): 王者之奕 - 赛季系统  本模块提供赛季系统功能： - Season: 赛季数据类 - SeasonReward: 赛季奖励 - PlayerSeasonDat, get_season_manager(), 王者之奕 - 赛季管理器  本模块提供赛季系统的管理功能： - SeasonManager: 赛季管理器类 - 获取当前赛季 - 计算赛季奖励 - 段位软重置逻, 创建新赛季          Args:             season_id: 赛季ID             name: 赛季名称, 获取指定赛季          Args:             season_id: 赛季ID          Returns:, 获取当前活跃赛季          Returns:             当前赛季对象，不存在返回None, 设置当前赛季          Args:             season_id: 赛季ID          Returns:, 结束指定赛季          Args:             season_id: 赛季ID          Returns: (+35 more)

### Community 25 - "Community 25"
Cohesion: 0.04
Nodes (44): create_equipment_manager(), create_equipment_service(), Equipment, EquipmentInstance, EquipmentManager, EquipmentService, EquipmentStats, from_dict() (+36 more)

### Community 26 - "Community 26"
Cohesion: 0.1
Nodes (16): _apply_assist_talent(), _apply_battle_talent(), _apply_economy_talent(), _apply_synergy_talent(), _apply_talent(), apply_to_player(), PlayerTalents, 天赋管理器      管理天赋配置、玩家天赋和效果应用。 (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (20): BaseSettings, 王者之奕 - 配置模块 ===================  提供配置管理和日志配置。  使用示例：     from config.settings im, DatabaseSettings, Environment, GameSettings, get_settings(), LogSettings, 王者之奕 - 配置管理模块 =======================  提供统一的配置管理，支持： - 环境变量读取 - 默认配置 - 配置验证 - 类型 (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (13): ComprehensiveStressTest, GamePhase, main(), 王者之奕 - 综合场景压力测试  模拟真实游戏场景： 1. 1000玩家同时在线 2. 100场对局同时进行 3. 完整游戏流程模拟 4. 观战系统并发访问, 模拟玩家操作          Returns:             (是否成功, 耗时ms), 模拟对局回合          Returns:             (是否成功, 耗时ms), 运行综合压力测试          Returns:             测试结果, 综合场景压力测试      模拟：     - 1000玩家同时在线     - 100场对局同时进行     - 匹配系统并发     - 观战系统负载 (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (15): do_run_migrations(), get_url(), include_object(), 王者之奕 - Alembic 环境配置  本模块配置 Alembic 迁移环境，支持： - 异步数据库迁移 - 自动生成迁移脚本 - 在线/离线迁移模式  使用, 执行迁移      Args:         connection: 数据库连接, 自定义类型渲染      用于处理自定义的 SQLAlchemy 类型。      Args:         type_: 类型名称         obj:, 过滤要包含在迁移中的对象      Args:         object: 数据库对象         name: 对象名称         type_:, 异步模式运行迁移      使用异步引擎连接数据库并执行迁移。 (+7 more)

### Community 30 - "Community 30"
Cohesion: 0.5
Nodes (1): 添加性能优化索引  Revision ID: perf_indexes_001 Revises: Create Date: 2026-02-22  优化数据库查

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): 王者之奕 - 集成测试模块  本模块包含所有集成测试： - test_friendship_integration: 好友系统 + 组队 + 私聊 - test

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): 生成数据库连接 URL          格式：mysql+aiomysql://user:password@host:port/name

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): 生成同步数据库连接 URL          格式：mysql+pymysql://user:password@host:port/name

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): 获取指定星级的合成配置          Args:             star_level: 星级          Returns:

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): 从字典反序列化          Args:             data: 状态字典          Returns:             经济管理

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): 从Emote创建消息数据          Args:             emote: 表情对象             from_player_id:

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): 从历史记录创建数据          Args:             history: 历史记录             emote: 表情对象

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): 从PrivateMessage创建消息数据

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): 创建新玩家的段位信息          Args:             player_id: 玩家ID          Returns:

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): 根据 ELO 分数获取对应段位          Args:             elo: ELO 分数          Returns:

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): 根据 ELO 和段位计算星级          Args:             elo: ELO 分数             tier: 段位

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): 从模板创建英雄实例          Args:             template: 英雄模板             instance_id: 实例I

## Knowledge Gaps
- **698 isolated node(s):** `Environment`, `王者之奕 - 配置管理模块 =======================  提供统一的配置管理，支持： - 环境变量读取 - 默认配置 - 配置验证 - 类型`, `数据库配置      环境变量：         DB_HOST: 数据库主机地址         DB_PORT: 数据库端口         DB_NAME`, `生成数据库连接 URL          格式：mysql+aiomysql://user:password@host:port/name`, `生成同步数据库连接 URL          格式：mysql+pymysql://user:password@host:port/name` (+693 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 30`** (4 nodes): `perf_indexes_001.py`, `downgrade()`, `添加性能优化索引  Revision ID: perf_indexes_001 Revises: Create Date: 2026-02-22  优化数据库查`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `王者之奕 - 集成测试模块  本模块包含所有集成测试： - test_friendship_integration: 好友系统 + 组队 + 私聊 - test`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `生成数据库连接 URL          格式：mysql+aiomysql://user:password@host:port/name`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `生成同步数据库连接 URL          格式：mysql+pymysql://user:password@host:port/name`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `获取指定星级的合成配置          Args:             star_level: 星级          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `从字典反序列化          Args:             data: 状态字典          Returns:             经济管理`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `从Emote创建消息数据          Args:             emote: 表情对象             from_player_id:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `从历史记录创建数据          Args:             history: 历史记录             emote: 表情对象`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `从PrivateMessage创建消息数据`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `创建新玩家的段位信息          Args:             player_id: 玩家ID          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `根据 ELO 分数获取对应段位          Args:             elo: ELO 分数          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `根据 ELO 和段位计算星级          Args:             elo: ELO 分数             tier: 段位`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `从模板创建英雄实例          Args:             template: 英雄模板             instance_id: 实例I`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Hero` connect `Community 1` to `Community 0`, `Community 4`, `Community 7`, `Community 8`, `Community 11`, `Community 25`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Session` connect `Community 6` to `Community 0`, `Community 3`, `Community 5`, `Community 7`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 15`, `Community 16`, `Community 17`, `Community 20`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `BaseMessage` connect `Community 0` to `Community 10`, `Community 12`, `Community 7`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `BaseMessage` (e.g. with `EquipmentWSHandler` and `王者之奕 - 装备系统 WebSocket 处理器  处理装备相关的 WebSocket 消息，包括： - 装备穿戴 - 装备卸下 - 装备合成 - 获取装备背`) actually correct?**
  _`BaseMessage` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 213 inferred relationships involving `Hero` (e.g. with `MockRoom` and `王者之奕 - pytest 配置和共享 fixtures  本模块提供测试所需的通用 fixtures，包括： - 测试用英雄数据 - 测试用玩家数据 - 测试`) actually correct?**
  _`Hero` has 213 INFERRED edges - model-reasoned connections that need verification._
- **Are the 213 inferred relationships involving `Session` (e.g. with `HeroShardWSHandler` and `王者之奕 - 英雄碎片系统 WebSocket 处理器  本模块实现英雄碎片系统的 WebSocket 消息处理： - 获取碎片背包 - 合成英雄 - 分解英雄`) actually correct?**
  _`Session` has 213 INFERRED edges - model-reasoned connections that need verification._
- **Are the 187 inferred relationships involving `Base` (e.g. with `MatchStatus` and `MatchRecordDB`) actually correct?**
  _`Base` has 187 INFERRED edges - model-reasoned connections that need verification._
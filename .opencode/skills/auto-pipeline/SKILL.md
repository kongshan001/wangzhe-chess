---
name: auto-pipeline
description: 自动化流水线，一键完成需求到部署的全流程
license: MIT
---

# 自动化流水线

## 概述

这是一个端到端的自动化流水线，只需要输入愿景，自动完成：
需求分析 → 代码实现 → 代码审核 → 测试覆盖 → 文档更新 → Git提交

## 使用方式

直接告诉 orchestrator 你的愿景，例如：

```
添加一个英雄装备系统，支持装备穿戴、卸下和合成
```

## 流水线阶段

### Stage 1: 需求分析 [planner]
```
输入: 用户愿景
处理: 分析需求，编写功能规格
输出: docs/requirements/<feature>.md
```

### Stage 2: 代码实现 [developer]
```
输入: docs/requirements/<feature>.md
处理: 实现功能代码
输出: 修改的源代码文件
```

### Stage 3: 代码审核 [code-reviewer]
```
输入: 代码变更
处理: 审核代码质量
输出: docs/reviews/<feature>.md
判断: 通过则继续，否则返回Stage 2
```

### Stage 4: 测试覆盖 [qa]
```
输入: 代码变更
处理: 编写测试用例
输出: tests/ 下的测试文件
验证: 覆盖率100%
```

### Stage 5: 文档更新 [doc-writer]
```
输入: 代码变更
处理: 更新相关文档
输出: 
  - docs/api/*.md
  - docs/architecture.md
  - docs/core-classes.md
```

### Stage 6: Git提交
```
输入: 所有变更
处理: 
  1. git add .
  2. git commit -m "feat: xxx"
  3. git push origin main
输出: 提交哈希
```

## 进度汇报格式

```
═══════════════════════════════════════
📊 自动化流水线进度
═══════════════════════════════════════

✅ Stage 1: 需求分析
   └─ 输出: docs/requirements/equipment-system.md

✅ Stage 2: 代码实现
   └─ 修改: src/server/game/equipment.py
   └─ 新增: src/server/api/equipment.py

✅ Stage 3: 代码审核
   └─ 状态: 通过
   └─ 报告: docs/reviews/equipment-review.md

✅ Stage 4: 测试覆盖
   └─ 覆盖率: 100%
   └─ 新增: tests/unit/test_equipment.py

✅ Stage 5: 文档更新
   └─ 更新: docs/api/equipment-api.md

✅ Stage 6: Git提交
   └─ 提交: abc1234
   └─ 推送: origin/main

═══════════════════════════════════════
🎉 流水线执行完成！
═══════════════════════════════════════
```

## 错误处理

- Stage 3 审核不通过 → 返回 Stage 2 修复
- Stage 4 测试失败 → 返回 Stage 2 修复
- Stage 6 推送失败 → 报告错误，手动处理

## 并行优化

独立任务可并行执行：
- Stage 3 + Stage 4 可以并行
- Stage 5 可以和 Stage 3/4 并行开始

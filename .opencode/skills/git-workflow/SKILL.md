---
name: git-workflow
description: Git工作流技能，规范化提交和推送
license: MIT
---

# Git工作流技能

## 触发场景

当需要提交代码并推送到远程仓库时使用。

## 提交规范

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 类型定义

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(hero): 添加英雄升级功能 |
| fix | 修复bug | fix(battle): 修复伤害计算错误 |
| docs | 文档变更 | docs: 更新API文档 |
| test | 测试相关 | test(hero): 添加英雄模块单元测试 |
| refactor | 重构 | refactor(economy): 优化经济系统计算 |
| perf | 性能优化 | perf(battle): 优化战斗模拟性能 |
| chore | 其他 | chore: 更新依赖版本 |

## 工作流程

### 1. 检查变更
```bash
git status
git diff
```

### 2. 暂存变更
```bash
git add <files>
# 或
git add .
```

### 3. 编写提交信息
```bash
git commit -m "type(scope): description"
```

### 4. 推送远程
```bash
git push origin <branch>
```

## 提交模板

### 功能提交
```
feat(module): 简短描述

- 详细说明1
- 详细说明2

Closes #issue_number
```

### 修复提交
```
fix(module): 简短描述

问题描述:
- 问题现象

修复方案:
- 修复方式

影响范围:
- 影响的模块
```

## 检查清单

- [ ] 所有文件已暂存
- [ ] 提交信息格式正确
- [ ] 无敏感信息泄露
- [ ] 测试已通过
- [ ] 文档已更新

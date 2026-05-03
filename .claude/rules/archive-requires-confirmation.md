# Archive Requires Confirmation

## 编号
R-005

## 描述
任务归档操作不允许自动执行。归档涉及将 worktree 中的代码合并到主干分支，是不可逆的关键操作，必须由用户明确授权。

具体规则:

**默认行为:**
- 创建任务时默认标记 `requires_archive_confirmation: true`
- 此字段写入 task JSON 文件（`.kanban/tasks/{task_id}.json`）

**归档操作范围:**
归档操作包括但不限于以下行为:
1. 将 worktree 的 git 分支合并到主干分支
2. 清理 worktree（删除 worktree 目录和相关元数据）
3. 将 task JSON 文件从 `tasks/` 移动到 `archive/`
4. 更新看板索引文件

**触发条件:**
- 用户必须通过显式执行 `/kanban decide {task_id} --action approve_and_archive` 来触发归档
- 不允许任何 agent、guard 或自动化流程绕过此确认直接执行归档

**禁止行为:**
- 禁止自动归档（auto-archive）
- 禁止在没有用户指令的情况下自动合并 worktree 到主干
- 禁止 agent 自行决定归档时机
- 禁止将 `requires_archive_confirmation` 默认设为 `false`

**例外情况:**
- 用户执行 `/kanban decide --action abort` 时，任务直接归档（不合并代码），此时不需要额外的归档确认，因为 abort 本身就是用户的明确决定

## 检查方法
Guard 在 archive 阶段执行以下检查:

1. 读取 task JSON 中的 `requires_archive_confirmation` 字段
2. 如果值为 `true`:
   - 检查 `user_decision` 阶段是否已完成
   - 检查是否存在用户执行 `approve_and_archive` 操作的记录（在 task JSON 的 `history` 中）
   - 验证 `user_decision.action` 字段为 `approve_and_archive`
3. 如果值为 `false`（仅限用户手动修改配置）:
   - 允许自动归档，但仍需记录操作日志
4. 缺失 `requires_archive_confirmation` 字段时，视为 `true`（安全默认）

## 违反后果
Guard 检测到未确认的归档请求时，阻止归档操作。系统输出警告信息:

```
GUARD BLOCKED: Archive requires user confirmation.
Task {task_id} has requires_archive_confirmation=true.
Please run: /kanban decide {task_id} --action approve_and_archive
```

任何试图绕过确认的归档操作都会被拦截，确保用户始终对代码合并到主干拥有最终控制权。此规则是框架的铁律之一，不可通过配置关闭。

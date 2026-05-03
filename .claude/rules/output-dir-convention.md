# Output Directory Convention

## 编号
R-001

## 描述
所有产出代码必须放在 `config.json` 中 `output_dir` 字段指定的根目录下的 `<task-name>/` 子目录中。

- `output_dir` 的值从 `.kanban/config.json` 的 `output_dir` 字段读取
- `<task-name>` 使用英文小写短横线命名（如 `snake`, `minesweeper`, `data-pipeline`）
- 完整路径模式: `{worktree_path}/{output_dir}/{task-name}/`
- 禁止将代码放在 worktree 根目录或其他未指定的位置

示例:
- `output_dir=games` 时，代码放 `games/snake/`、`games/minesweeper/`
- `output_dir=scripts` 时，代码放 `scripts/data-pipeline/`
- `output_dir=src`（默认值）时，代码放 `src/my-feature/`

此规则适用于所有由 executor agent 产出的代码文件，包括源代码、测试文件、配置文件和静态资源。唯一的例外是框架本身（`.claude/` 和 `.kanban/` 目录）的增强任务，这类任务不产出应用代码。

## 检查方法
executor agent 完成编码后，`guard_check_artifacts` 函数扫描 worktree 中的文件变更，验证所有新增或修改的文件均位于 `{output_dir}/{task-name}/` 路径下。具体检查逻辑:

1. 读取 `.kanban/config.json` 中的 `output_dir` 值
2. 读取 `task_breakdown.json` 中 planner 确定的 `task-name`
3. 列出 worktree 中所有变更文件
4. 验证每个文件是否在 `{output_dir}/{task-name}/` 目录内
5. 排除 `.claude/` 和 `.kanban/` 目录（框架文件不受此规则约束）

## 违反后果
`guard_check_artifacts` 检测到文件位于错误位置时，阻止任务进入下一阶段（evaluate）。系统输出错误信息，列出所有违规文件及其当前位置和期望位置。executor agent 必须将文件移动到正确位置后才能继续流程。

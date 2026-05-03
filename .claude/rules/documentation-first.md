# Documentation First

## 编号
R-003

## 描述
每个阶段必须产出对应的文档产物。文档不是可选的附属品，而是流程推进的必要条件。

各阶段要求的文档产物:

**Plan 阶段:**
- `requirements.md` -- 需求分析文档，包含功能需求、非功能需求、技术约束和验收标准
- `task_breakdown.json` -- 任务拆解，包含 subtask 列表、优先级、依赖关系和预估文件

**Execute 阶段:**
- `execution_summary.md` -- 执行总结，包含完成内容、实现决策、测试结果和已知问题
- `execution_pitfalls.md` -- 遇到的问题和解决方法记录
- `execution_decisions.md` -- 技术决策及其原因

**Evaluate 阶段:**
- `code_reviewer_report.json` -- 代码审核报告
- `qa_report.json` -- QA 测试报告
- `pm_report.json` -- 产品经理评审报告
- `designer_report.json` -- 设计评审报告

此规则确保流程全程可追溯、可复盘。文档是后续迭代改进和知识沉淀的基础数据来源。

## 检查方法
`guard_check_artifacts` 函数在各阶段转换时验证产物完整性:

1. Plan -> Execute 转换时，检查 `requirements.md` 和 `task_breakdown.json` 存在且非空
2. Execute -> Evaluate 转换时，检查 `execution_summary.md`、`execution_pitfalls.md` 和 `execution_decisions.md` 存在且非空
3. Evaluate -> User Decision 转换时，检查 4 个角色报告 JSON 文件存在且包含有效评分

每个检查点验证:
- 文件物理存在
- 文件大小大于 0 字节
- JSON 文件可通过 `jq` 解析
- Markdown 文件包含至少一个非空标题

## 违反后果
Guard 检测到产物缺失时，阻止阶段转换。系统输出明确的错误信息，指出缺失的文件名和当前阶段。相关 agent（planner / executor / evaluator）必须补全缺失的文档产物后才能继续流程。如果 agent 无法在 2 次重试内补全，将任务标记为 `error` 状态并通知用户介入。

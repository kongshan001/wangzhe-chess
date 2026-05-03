# Agent Scheduling Coverage

## 编号
R-002

## 描述
评估阶段（evaluate phase）必须调度全部 4 个评估角色，不允许跳过任何角色。

四个评估角色及其职责:
- **code_reviewer**: 审核架构设计、代码质量、安全性和测试覆盖率
- **qa**: 验证测试完整性、边界覆盖、错误处理和验收标准
- **pm**: 验证需求覆盖、用户体验、功能完整性和验收标准
- **designer**: 评审 API 设计、模块结构、可扩展性和一致性

此规则确保每次迭代都经过完整的多维度评估，避免因省略某个角色而遗漏问题。即使任务看似只涉及某个领域（如纯逻辑任务），仍需全部 4 个角色参与评估，因为跨角色评审能发现单一视角无法察觉的问题。

4 个评估 agent 通过 `run_in_background=true` 参数并行启动，以减少评估阶段的总耗时。

## 检查方法
evaluate 阶段完成后，`guard_check_evaluation` 函数检查是否生成了全部 4 个角色的报告 JSON 文件:

1. 检查 `{report_dir}/code_reviewer_report.json` 是否存在且包含有效评分
2. 检查 `{report_dir}/qa_report.json` 是否存在且包含有效评分
3. 检查 `{report_dir}/pm_report.json` 是否存在且包含有效评分
4. 检查 `{report_dir}/designer_report.json` 是否存在且包含有效评分
5. 验证每个报告包含必需字段: `role`, `task_id`, `iteration`, `scores`, `summary`

缺失任何一个报告文件均视为违反此规则。

## 违反后果
`guard_check_evaluation` 检测到缺失报告时，阻止流程进入 user_decision 阶段。系统输出错误信息，列出缺失的角色报告。编排器必须重新调度缺失角色的评估 agent，补全报告后才能继续。如果某个 agent 反复失败，记录到任务 history 中并通知用户。

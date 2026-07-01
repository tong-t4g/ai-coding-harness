---
name: change-summary
description: 在 review 或提 PR 前，整理一份变更摘要
---
# 生成变更摘要
## 输入
`$ARGUMENTS` = OpenSpec 的 change id
## 必读文件
- `openspec/changes/$ARGUMENTS/proposal.md`
- `openspec/changes/$ARGUMENTS/design.md`
- `openspec/changes/$ARGUMENTS/tasks.md`
- 相关源码改动
- `docs/standards/testing.md`
- `docs/standards/database.md`
## 输出内容
- 本次变更的目标
- 影响到的类和模块
- 是否涉及接口、事务、SQL、配置
- 已运行测试
- 已知风险
- 仍未解决的问题
## 规则
- 不要写空洞表扬
- 保持简洁、事实化
- 优先标出风险和未完成项

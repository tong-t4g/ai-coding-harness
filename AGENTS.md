# AGENTS.md
## 项目说明
本仓库采用 Harness 风格工作流：
- OpenSpec 负责定义需求与变更制品
- Codex 在项目规则内执行
- 实现与评审分离
- Hooks、权限和 CI 负责硬约束
## 首先阅读
1. `docs/architecture/index.md` -- 架构规则
2. `docs/product/index.md` -- 产品规则
3. `docs/standards/testing.md` -- 测试规则
4. `docs/standards/database.md` -- 数据库与 SQL 规则
5. `openspec/specs/`
6. `openspec/changes/<change-id>/`
7. `docs/architecture/implicit-contracts.md` -- 业务隐性规则
## 工作规则
- 没有 OpenSpec change，不允许直接开始开发
- 修改代码前，先总结本次需求范围
- 只允许实现 `tasks.md` 中明确列出的内容,不允许自行扩散需求
- 每完成一个里程碑，都必须运行相关检查
- 修改数据库、配置、高风险业务时，必须明确说明影响范围
- 合并前必须经过 review 和 verify
- 最终输出简短总结，包括：
  - 改动了哪些类/文件
  - 跑了哪些测试
  - 还存在哪些风险
## 主流程命令
- 新需求：`/opsx:propose`
- 实施：`/opsx:apply`
- 校验：`/opsx:verify`
- 归档：`/opsx:archive`
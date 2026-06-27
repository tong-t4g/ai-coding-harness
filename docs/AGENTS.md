# AGENTS.md
## 项目说明
本仓库采用 harness 风格工作流：
- OpenSpec 负责定义需求与变更工件
- Claude Code 在项目规则内执行
- 实现与评审分离
- Hooks、权限和 CI 负责硬约束
## 首先阅读
1. `docs/architecture/index.md`
2. `docs/product/index.md`
3. `docs/standards/testing.md`
4. `docs/standards/database.md`
5. `openspec/specs/`
6. `openspec/changes/<change-id>/`
7. `docs/architecture/implicit-contracts.md`
## 工作规则
- 没有 OpenSpec change，不允许直接开始开发
- 不允许超出 `tasks.md` 自行扩需求
- 每完成一个里程碑，都必须运行相关检查
- 修改数据库、配置、高风险业务时，必须明确说明影响范围
- 合并前必须经过 review 和 verify
## 受保护目录
- `src/main/resources/application*.yml`
- `src/main/resources/bootstrap*.yml`
- `src/main/resources/db/`
- `sql/`
- `deploy/`
- `infra/`
- `secrets/`
## 主流程命令
- 新需求：`/opsx:propose`
- 实施：`/opsx:apply`
- 校验：`/opsx:verify`
- 归档：`/opsx:archive`
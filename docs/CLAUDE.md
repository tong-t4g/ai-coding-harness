@AGENTS.md
# Claude Code 项目规则
## 你的角色
你是一个在 harness 工作流中执行实现和评审任务的代理。
## 必须遵守的工作流程
1. 开始实现前，必须先阅读对应的 OpenSpec change：
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/design.md`
- `openspec/changes/<change-id>/tasks.md`
2. 修改代码前，先总结本次需求范围
3. 只允许实现 `tasks.md` 中明确列出的内容
4. 每完成一个里程碑，必须执行相关检查
5. 最终输出简短总结，包括：
- 改动了哪些类/文件
- 跑了哪些测试
- 还存在哪些风险
## Spring Boot 架构规则
- Controller 只负责参数接收、返回结果，不写核心业务逻辑
- 业务逻辑必须放在 Service / Domain 层
- Controller 不允许直接调用 Mapper / Repository
- Service 不允许直接依赖 Web 层对象
- DTO/VO 不允许直接当作持久化实体使用
- 涉及数据库查询变更时，必须关注索引、分页、条件范围和 N+1 风险
- 新增外部依赖时，必须在 design.md 中说明理由
## 测试规则
- 任何行为变化都必须补充至少一个相关测试
- Service 层变更优先补单元测试
- Controller/API 行为变更优先补集成测试
- Bug 修复在条件允许时必须补 regression test
- 修改 SQL / Mapper 时，必须至少说明验证方式
## 事务与数据规则
- 涉及写操作时，必须明确事务边界
- 不允许无条件全表更新/删除
- 批量操作必须说明范围控制条件
- 修改数据库脚本、迁移文件、核心 SQL 时必须谨慎，必要时停止并请求确认
## 安全规则
- 除非 OpenSpec design 明确要求，否则不允许修改：
- `src/main/resources/application*.yml`
- `src/main/resources/bootstrap*.yml`
- `src/main/resources/db/`
- `sql/`
- `deploy/`
- `infra/`
- `secrets/`
- 不允许执行部署、推送、生产环境相关命令
- 如果需求边界不清楚，应停止并报告，不允许自行脑补需求
## 常用命令（Maven）
- 编译：`mvn -q -DskipTests compile`
- 单测：`mvn test`
- 打包：`mvn -DskipTests package`
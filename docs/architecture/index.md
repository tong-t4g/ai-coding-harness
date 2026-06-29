# 架构规则
## 架构规则
- 新增外部依赖时，必须在 design.md 中说明理由
## 职责分层
- `controller`：接口层，负责请求接收、参数校验、响应封装
- `service`：业务编排层，负责核心业务流程
- `domain/entity`：领域对象或实体对象
- `repository/mapper`：数据访问层
- `config`：框架和中间件配置
- `job` / `scheduler`：定时任务
## 依赖方向
- controller -> service -> repository/mapper
- controller 不允许直接调用 mapper/repository
- repository/mapper 不允许反向依赖 service
- service 不允许直接依赖 Web 层对象
- web 层对象不允许深入渗透到持久化层
## 事务与数据规则
- 涉及写操作时，必须明确事务边界
- 不允许无条件全表更新/删除
- 批量操作必须说明范围控制条件
- 修改数据库脚本、迁移文件、核心 SQL 时必须谨慎，必要时停止并请求确认
- 涉及数据库查询变更时，必须关注索引、分页、条件范围和 N+1 风险
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
## 测试规则
- 任何行为变化都必须补充至少一个相关测试
- Service 层变更优先补单元测试
- Controller/API 行为变更优先补集成测试
- Bug 修复在条件允许时必须补 regression test
- 修改 SQL / Mapper 时，必须至少说明验证方式
## 常用命令（Maven）
- 编译：`mvn -q -DskipTests compile`
- 单测：`mvn test`
- 打包：`mvn -DskipTests package`
## 高风险区域
以下区域修改时必须重点说明：
- 支付/订单
- 认证/鉴权
- 定时任务
- 数据迁移
- 批量更新/批量删除
- 核心 SQL
## 变更设计要求
如果 change 涉及高风险区域，design.md 中必须说明：
- 影响的类和模块
- 事务边界
- SQL / 索引 / 查询范围影响
- 回滚方案
- 测试策略
# 架构总览
## 系统分层
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
- web 层对象不允许深入渗透到持久化层
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
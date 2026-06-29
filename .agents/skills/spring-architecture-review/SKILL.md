---
name: spring-architecture-review
description: 检查 Spring Boot 分层、依赖方向和业务逻辑放置是否合理
disable-model-invocation: true
---
# Spring 架构审查
## 输入
`$ARGUMENTS` = 本次改动涉及的文件、目录或 change id
## 检查项
1. Controller 是否写入了业务逻辑
2. Controller 是否直接调用 Mapper / Repository
3. Service 是否依赖了 Web 层对象
4. DTO/VO 是否被直接当作实体持久化
5. 是否存在明显的跨层耦合
6. 是否有可以归为 Domain/Service 的逻辑散落在其他层
## 输出格式
- 严重问题
- 警告问题
- 建议项
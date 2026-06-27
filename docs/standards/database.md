# 数据库与 SQL 规范
## 基本规则
- 不允许无条件 UPDATE / DELETE
- 批量更新必须明确 where 条件和影响范围
- 分页查询必须明确排序条件
- 不允许在高频接口中引入明显的 N+1 查询
- 修改 Mapper / XML / SQL 时，必须关注索引命中情况
## 必须说明的内容
以下场景必须在 design.md 或 review 摘要中说明：
- 是否影响索引
- 是否会放大扫描范围
- 是否会引入锁竞争
- 是否需要数据修复或迁移
- 是否影响历史数据兼容性
## 高风险目录
- `**/src/main/resources/mapper/`
- `**/src/main/resources/db/`
- `sql/`
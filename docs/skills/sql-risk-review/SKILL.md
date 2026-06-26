---
name: sql-risk-review
description: 检查 SQL、Mapper、批量更新、分页和索引相关风险
disable-model-invocation: true
---
# SQL 风险审查
## 输入
`$ARGUMENTS` = 本次改动涉及的 SQL、Mapper、XML、Repository 文件
## 检查项
1. 是否存在无条件更新/删除
2. 批量更新是否有清晰范围
3. 分页是否有稳定排序
4. 是否可能放大扫描范围
5. 是否存在明显的 N+1 风险
6. 是否缺少索引影响说明或验证方式
## 输出格式
- 严重问题
- 警告问题
- 建议项
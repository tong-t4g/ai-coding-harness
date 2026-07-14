# 测试规则
## 最低要求
- 行为变化：至少补 1 个相关测试
- Bug 修复：优先补 regression test
- Service 层逻辑修改：优先补单元测试
- Controller/API 改动：如适用，补集成测试
- 核心 SQL 改动：至少说明验证方法和边界数据
## 常用命令（Maven）
- 单元测试：`mvn test`
- 编译检查：`mvn -q -DskipTests compile`
- 打包检查：`mvn -DskipTests package`
## 评审要求
提交 review 时必须说明：
- 跑了哪些测试
- 哪些部分没有测
- 为什么跳过这些检查仍然可以接受
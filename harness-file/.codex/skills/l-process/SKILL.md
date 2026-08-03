---
name: l-process
description: "基于规格或一组任务单实现一项工作。"
disable-model-invocation: true
---

实现用户在规格或任务单中描述的工作。

在预先约定的测试接缝上，尽可能使用 `/tdd`。

定期运行类型检查和单个测试文件；最后运行一次完整测试套件。

完成后使用 `/code-review` 审查工作。

将工作提交到当前分支。

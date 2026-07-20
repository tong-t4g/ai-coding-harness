---
name: l-process
description: 基于用户的需求描述实现并交付开发工作（轻量流程）
disable-model-invocation: true
---

基于用户的需求描述，实现相应的开发工作。

尽可能在预先认可的 seams 上使用 `/tdd`。

定期运行类型检查 (Typechecking)，频繁运行单文件测试 (Single test files)，并在开发结束前完整执行一次全量测试套件 (Full test suite)。

开发完成后，调用代码评审指令 (/code-review) 对产出工作进行代码审查。

最后，将你的工作成果提交 (Commit) 到当前分支。

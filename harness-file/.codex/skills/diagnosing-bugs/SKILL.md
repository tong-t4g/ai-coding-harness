---
name: diagnosing-bugs
description: 用于诊断复杂 Bug 和性能回归的闭环流程。当用户说“诊断”“调试这个”，或报告功能损坏、抛错、失败、变慢时使用。
---

# 诊断 Bug

用于处理复杂 Bug 的纪律化流程。只有给出明确理由时，才允许跳过阶段。

探索代码库时，如果存在 `CONTEXT.md`，先阅读它以建立相关模块的清晰心智模型；同时检查正在修改区域的 ADR。

## 阶段 1：建立反馈闭环

**这就是本 skill 的核心。** 其余内容都是机械执行。如果有一个针对**这个具体 Bug**的紧凑通过/失败信号，并且它能在该 Bug 上变红，就能找到根因；二分、假设验证和插桩都只是消费这个信号。如果没有它，盯着代码再久也无法解决问题。

在这里投入不成比例的精力。**主动尝试、发挥创造力，不要轻易放弃。**

### 构建反馈闭环的方法（大致按以下顺序尝试）

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) — drives the UI, asserts on DOM/console/network.
5. **Replay a captured trace.** Save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Spin up a minimal subset of the system (one service, mocked deps) that exercises the bug code path with a single function call.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.
10. **人工介入 Bash 脚本。** 最后手段。如果必须由人点击，就用 `scripts/hitl-loop.template.sh` 驱动人工介入，使闭环仍保持结构化；捕获的输出要回流到诊断过程。

建立正确的反馈闭环，Bug 就已经解决了 90%。

### 收紧闭环

把闭环当成产品来打磨。建立一个闭环后，继续**收紧**它：

- Can I make it faster? (Cache setup, skip unrelated init, narrow the test scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

一个耗时 30 秒且不稳定的闭环，几乎不比没有闭环好；一个耗时 2 秒且确定性的闭环才算紧凑，是调试的强力杠杆。

### 非确定性 Bug

目标不是得到一次完美复现，而是提高**复现率**。将触发条件循环 100 次、并行执行、增加压力、缩小时间窗口、注入 sleep。复现率 50% 的 Bug 可以调试，1% 的不行；持续提高复现率，直到具备可调试性。

### 确实无法建立闭环时

停止并明确说明。列出已尝试的方案，请用户提供以下之一：(a) 可复现问题的环境访问权限；(b) 捕获的产物（HAR 文件、日志转储、core dump、带时间戳的录屏）；或 (c) 添加临时生产环境插桩的权限。没有闭环时，**不要**继续凭空提出假设。

### 完成标准：能变红的紧凑闭环

阶段 1 在闭环**紧凑**且**具备变红能力**时完成：必须能指出**一条命令**（脚本路径、测试调用或 curl），该命令已经**至少实际运行过一次**（粘贴调用和输出），并满足：

- [ ] **可变红**：驱动真实 Bug 代码路径，并断言**用户描述的确切症状**，修复前变红、修复后变绿。不是“运行不报错”，而是必须能捕获**这个具体 Bug**。
- [ ] **确定性**：每次运行得到相同结论（对于不稳定 Bug，按上文提高并固定复现率）。
- [ ] **快速**：耗时应为秒级，而不是分钟级。
- [ ] **可由 Agent 执行**：可无人值守运行；只有通过 `scripts/hitl-loop.template.sh` 时才允许人工介入。

如果在这条命令建立前就开始阅读代码构建理论，**立即停止——直接跳到假设正是本 skill 要阻止的失败模式。** 没有能变红的命令，就不能进入阶段 2。

## 阶段 2：复现并最小化

运行闭环，观察它变红，即确认 Bug 出现。

确认：

- [ ] 闭环产生的是**用户**描述的失败模式，而不是碰巧相邻的另一种失败。Bug 找错，修复就会错。
- [ ] 失败可在多次运行中复现（非确定性 Bug 则达到足以调试的复现率）。
- [ ] 已捕获确切症状（错误信息、错误输出或慢速耗时），后续阶段才能验证修复确实解决了问题。

### 最小化

变红后，将复现缩小到**仍能变红的最小场景**。逐次删减输入、调用方、配置、数据和步骤，每次删减后都重新运行闭环，只保留对失败起决定作用的部分。

这样做的原因是：最小复现能缩小阶段 3 的假设空间（可疑活动部件更少），并可在阶段 5 转化为干净的回归测试。

当**每个保留元素都不可再删减**时完成；删除任意一个元素都会让闭环变绿。

未完成复现和最小化前，不得继续。

## 阶段 3：提出假设

在测试任何假设前，先生成 **3～5 个有排序的假设**。只生成一个假设会让判断锚定在第一个看似合理的想法上。

每个假设都必须**可证伪**：明确写出它所预测的结果。

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

如果无法写出预测，这个假设只是感觉；丢弃它或把它具体化。

**测试前向用户展示排序后的列表。** 用户往往有领域知识，可以立即重新排序（“我们刚部署了第 3 项变更”），或者知道哪些假设已经排除。这是成本很低但节省大量时间的检查点。不要因此阻塞；如果用户暂时不在线，就按当前排序继续。

## 阶段 4：插桩验证

每次探测都必须对应阶段 3 的一个具体预测。**一次只改变一个变量。**

工具优先级：

1. 如果环境支持，优先使用**调试器 / REPL 检查**。一个断点胜过十条日志。
2. 在能区分不同假设的边界添加**定向日志**。
3. 绝不要“把所有东西都打日志再 grep”。

**为每条调试日志添加唯一前缀**，例如 `[DEBUG-a4f2]`。收尾时一次 grep 即可清理。未标记的日志可能残留，带标记的日志必须删除。

**性能分支。** 对性能回归，日志通常不是正确工具。应先建立基线测量（计时 harness、`performance.now()`、性能分析器或查询计划），再执行二分。先测量，后修复。

## 阶段 5：修复并添加回归测试

在修复前编写回归测试，但前提是存在**正确的测试接缝（seam）**。

正确的测试接缝是指：测试能在真实调用点复现实际 Bug 模式。如果唯一可用的接缝过浅（Bug 需要多个调用方却只测试单个调用方，或单元测试无法复现触发 Bug 的调用链），在那里添加回归测试只会制造虚假的安全感。

**不存在正确接缝本身就是一个发现。** 记录下来：代码库架构阻止了该 Bug 被可靠固化。把它标记给下一阶段处理。

如果存在正确接缝：

1. 将最小复现转化为该接缝上的失败测试。
2. 观察测试失败。
3. 应用修复。
4. 观察测试通过。
5. 针对原始（未最小化）场景重新运行阶段 1 的反馈闭环。

## 阶段 6：清理与复盘

宣布完成前必须满足：

- [ ] 原始复现不再出现（重新运行阶段 1 的闭环）
- [ ] 回归测试通过（或已记录不存在合适接缝）
- [ ] 所有 `[DEBUG-...]` 插桩已删除（grep 该前缀确认）
- [ ] 一次性原型已删除，或移动到明确标记的调试目录
- [ ] 在 commit / PR 信息中写明最终证实的假设，让下一个调试者获得上下文

**然后追问：什么本可以阻止这个 Bug？** 如果答案涉及架构变更（没有合适的测试接缝、调用方纠缠或隐式耦合），将具体信息交接给 `/improve-codebase-architecture` skill。必须在修复完成后再给出建议，而不是之前；此时掌握的信息更多。

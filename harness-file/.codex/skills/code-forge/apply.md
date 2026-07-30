# CodeForge:apply — 构建阶段

## 目标

实现 propose 阶段生成的实现计划。本阶段是编排层，实际执行和审查由其它 skill 完成。

## 前置检查

1. 确认 `openspec/plans/` 下有实现计划文件（`YYYY-MM-DD-<变更名>.md`）
2. 如果没有实现计划文件，但有 `openspec/changes/` 下的活跃变更 → 提示用户：`回到 /code-forge 进入 propose 阶段完成计划生成`
3. 读取 `.codeforge-state.yaml` 的 `project_profile`，获取 `compile_command` 和 `test_command`

## 环境检查

在开始实现前，验证编译环境是否可用：

1. **验证编译**：运行 `compile_command`（来自 project_profile）
   - 如果 compile_command 为 null（如纯 Python/前端项目），跳过编译检查
   - 如果编译失败且原因是环境问题（如 JDK 版本不匹配、Node 版本不匹配），**立即阻塞并报告**，等待用户确认
   - 如果编译失败是代码问题，正常进入实现阶段（TDD 会逐步修复）

## 智能执行模式选择

根据多因子分析选择最优执行模式，不再使用简单的任务数量阈值：

| 因子 | 权重 | 检测方式     |
|------|------|----------|
| 任务数量 | 高 | 统计计划文件中的 `### 任务 N` 标题 |
| 执行单元 | 高 | 根据计划中的前置任务和关联文件聚合 |
| 跨模块性 | 中 | 分析实现计划文件中 File Structure 涉及的模块/目录数量 |
| 项目结构 | 中 | `project_profile.structure`：monorepo 倾向完整模式 |
| 变更复杂度 | 低 | 预估涉及修改的文件数量 |

**先确定执行单元：**

1. 以计划 Task 为节点；两个 Task 存在直接前置依赖，或 `关联文件` 中出现同一文件时连边。比较文件前，把 `\` 转为 `/`、去掉末尾 `:行号` 或 `:起始-结束`，并使用 Git 中的仓库相对路径大小写。
2. 每个无向连通分量是一个执行单元。单元内按依赖拓扑顺序执行，无依赖关系时按计划编号；依赖环是计划缺陷，必须显式阻塞并修正计划。
3. 按分量中的最小 Task 编号为执行单元排序。不同执行单元必须没有依赖和文件重叠；声明不完整时回到 propose 修正计划，不能猜测并行安全性。

**决策规则：**

- **轻量模式**（inline 执行）：单 Task 小功能，或非 monorepo 且任务 ≤ 3、修改集中在 1-2 个模块。
- **完整模式**（subagent-implement）：不满足轻量模式，且主工作树干净、计划文件和状态文件已提交。执行单元只有一个时，使用一个 subagent/worktree 在内部顺序执行；有两个以上执行单元时，单元之间并行。

任务依赖、共享文件或强编译依赖只决定执行单元边界，不再直接迫使流程降级为轻量模式。若规模需要完整模式但其工作树前置条件不满足，先完成限定范围的准备提交或显式阻塞，不得仅为绕过前置条件改用轻量模式。

## 阶段流程

**重要：** 完整模式在执行单元 worktree 内保持“一个 Task 一个提交”，集成到主工作树时形成“一个执行单元一个提交”；轻量模式保持“一个 Task 一个提交”。每个 fix 单独提交。commit 前必须执行编译检查且编译通过，全程不做自动 push 操作。

**断点检测（阶段流程入口）：**

从 `.codeforge-state.yaml` 读取 checkpoint，然后验证实际状态：

| checkpoint | 实际状态验证 | 路由到 |
|-----------|-------------|--------|
| `plan-generated-and-confirmed` | 计划文件有 checkbox 且全部未勾选 | Step 1（全新执行） |
| `plan-generated-and-confirmed` | 计划文件有 checkbox 且部分已勾选 | Step 1（断点恢复，从第一个未勾选继续） |
| `unit-N-complete` | 清单中 unit-N 已记录集成提交，且其全部 Task checkbox 已勾选 | Step 1（从下一个未集成执行单元继续） |
| `unit-N-complete` | 清单记录或任一所属 Task checkbox 不一致 | Step 1（回退到上一个确认一致的执行单元） |
| `task-N-complete` | 计划文件中 task N 的 checkbox 确实已勾选 | Step 1（从 task N+1 继续） |
| `task-N-complete` | 计划文件中 task N 的 checkbox 未勾选（状态文件过期） | Step 1（回退到上一个确认一致的 task） |
| `verified` | 所有 checkbox 勾选 + 测试通过 | Step 3（审查） |
| `verified` | 测试未通过 | Step 1（从失败点修复，重新走提交流程） |
| `reviewed` | 所有 checkbox 勾选 + 审查通过 | Step 4（最终确认） |
| `reviewed` | 审查仍有 Critical 问题未修复 | Step 1（修复审查问题） |

### 1. 执行实现

**完整模式**：
调用 `subagent-implement` skill 执行实现：
- 使用 `openspec/plans/` 下的计划文件作为输入
- 若计划或状态文件尚未提交，先将它们提交为 `chore(codeforge): prepare <变更名> apply`；不得夹带其它改动
- 按前述固定规则聚合任务，为每个执行单元创建一个专属 Git worktree；两个以上执行单元在平台并发上限内并行分派
- 每个执行单元由一个实现者按任务序列顺序实现；每个 Task 完成验证后在单元 worktree 中单独提交
- 每个执行单元在自己的 worktree 中完成整体审查和修复复审
- 子智能体不得修改共享计划和状态文件；worktree 审查通过不等于执行单元已完成
- 所有执行单元审查通过后，主会话按单元编号串行集成；每次集成后才更新该单元全部 Task 的 checkbox 和 checkpoint，并生成最终执行单元 commit
- 集成冲突、组合编译失败或 worktree 清理失败都必须显式阻塞

**轻量模式**：
在当前会话中直接执行：
- 按 `openspec/plans/` 下的计划文件逐个 Task 执行
- 严格遵循计划文件中每个 Step 的 checkbox 顺序
- 每个 Task 完成后执行收尾流程

**每个执行单元或轻量任务完成后的提交流程：**

完整模式由 `subagent-implement` 执行以下流程；轻量模式由当前会话直接执行：

1. **取得改动**：完整模式从已审查的执行单元 worktree 运行 `execution-worktree integrate PLAN_FILE unit-N`；轻量模式使用当前工作树中的实现改动
2. **编译检查**：运行 `compile_command`，编译必须通过（如果 compile_command 为 null 则跳过）
3. **更新 checkbox**：完整模式将该执行单元包含的**所有 Task 下的全部** `- [ ]` 改为 `- [x]`；轻量模式更新当前 Task。包括 Verify、Commit 等非实现步骤，不能遗漏
4. **更新状态文件**：完整模式更新为 `checkpoint: unit-N-complete`；轻量模式更新为 `checkpoint: task-N-complete`
5. **自动 commit**：将代码改动 + 计划文件变更 + 状态文件变更一起提交到本地仓库
   - commit message 格式：`<类型>(<范围>): <执行单元或 task 描述>`
   - 完整模式一个执行单元对应一个最终 commit；轻量模式一个 Task 对应一个 commit
   - **全程不做 push 操作**
6. **记录集成**：完整模式运行 `execution-worktree record PLAN_FILE unit-N HEAD`；轻量模式跳过

**原子性保证**：先取得代码改动，再更新 checkbox 和状态文件，最后一起 commit。完整模式如果在 `integrate` 后、commit 前中断，主工作树会保留暂存改动；恢复时核对差异后继续编译和提交，不得重复集成。如果 commit 后、`record` 前中断，直接补记集成提交。如果 commit 和记录均完成，checkpoint、checkbox 和 worktree 清单共同证明该执行单元已完成。

### 2. 验证完成

调用 `verify` skill：
- 运行 `test_command`（来自 project_profile），如果 test_command 为 null 则跳过自动化测试
- 确认结果符合预期

验证通过后更新 `.codeforge-state.yaml`：`checkpoint: verified`。

### 3. 全局审查

全部任务完成后，调用 `code-review` skill 做一轮全局代码审查。

如果审查发现 Critical 或 Important 问题，逐项修复。每个 fix 的提交流程：
1. 编译检查 → 必须通过
2. 自动 commit → 格式：`fix(<范围>): <fix描述>`

修复完成后回到 Step 2(验证完成) 重新验证，再重新审查(Step 3)，直到审查通过。

**重试上限**：如果全局审查循环超过 3 次仍有 Critical 问题，提示用户：「审查反复不通过，可能需要回到 propose 阶段重新审视设计方案。」让用户决定是否继续。

审查通过后更新 `.codeforge-state.yaml`：`checkpoint: reviewed`。

### 4. 最终确认

Step 2 验证通过 + Step 3 审查通过后：

1. **同步 tasks.md 状态**：将 `openspec/changes/<变更名>/tasks.md` 中所有任务的完成状态标记为已完成（与 openspec/plans 中的 checkbox 状态对齐）
2. 向用户展示变更摘要（改动文件列表、commit 列表、验证结果、审查结论）

此步骤是 apply 阶段的最终出口，完成后更新 `.codeforge-state.yaml`：`phase: archive`、`checkpoint: apply-done`，然后自动进入 archive 阶段。

## 出口条件

- `openspec/plans/` 下的计划文件中所有 checkbox 已勾选
- 全量编译通过（或 compile_command 为 null）
- 测试全部通过（或 test_command 为 null）
- 代码审查无 Critical 级别问题
- `openspec/changes/<变更名>/tasks.md` 中所有任务标记为已完成（在 Step 4 统一同步）

## 断点恢复

1. **计划文件完整性**：如果计划文件存在但不完整（缺少头部或 checkbox），提示用户回到 propose 阶段重新生成
2. **状态文件过期**：轻量模式按 Task checkbox 核对；完整模式同时核对执行单元清单、集成提交和该单元全部 Task checkbox。不一致时回退到上一个确认一致的 checkpoint
3. **完整模式 worktree 状态**：同时读取 worktree 清单和进度账本；已审查但未集成的执行单元从串行集成继续，已提交但未记录的执行单元补跑 `record`
4. **环境检查**：断点恢复时跳过环境检查（已在首次运行时验证），直接进入执行

## 审查循环

如果执行单元审查者打回某个执行单元：
1. 实现者根据反馈修改
2. 重新提交审查
3. 循环直到通过

如果同一执行单元修改 3 次以上仍不通过，提示用户：「这个执行单元反复审查不通过，可能需要回到 propose 阶段重新审视设计方案。」

## 硬门

本阶段**禁止修改规格设计文档**（openspec/changes/ 下的 proposal.md、design.md、specs/）。如果实现过程中发现规格有问题，记录下来留到 archive 阶段处理。

**例外：** `tasks.md` 中的任务完成状态可在 Step 4 同步更新（仅限状态标记，不修改任务内容）。

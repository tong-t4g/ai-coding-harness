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
| 任务数量 | 高 | 读取计划文件 checkbox 数量 |
| 任务独立性 | 高 | 分析 tasks.md 中任务间的依赖关系 |
| 跨模块性 | 中 | 分析实现计划文件中 File Structure 涉及的模块/目录数量 |
| 项目结构 | 中 | `project_profile.structure`：monorepo 倾向完整模式 |
| 变更复杂度 | 低 | 预估涉及修改的文件数量 |

**决策规则：**

- **完整模式**（subagent-implement）：必须先满足以下全部硬条件
  - 所有任务都能从同一个分支起点独立实现、编译和验证
  - 任务之间没有输入依赖，也不修改同一文件
  - 主工作树干净，计划文件和状态文件已提交

  满足硬条件后，再满足以下任一规模条件：
  - 任务 ≥ 6
  - 涉及 ≥ 3 个不同模块/目录的修改
  - monorepo 结构 + 任务 ≥ 3
  - 任务 ≥ 4
- **轻量模式**（inline 执行）：满足以下任一条件
  - 任务 ≤ 3 且集中在 1-2 个模块
  - 单任务小功能
  - 任务之间存在输入依赖、共享文件修改或强编译依赖（需要顺序执行）

**冲突裁定：** 完整模式的独立性硬条件优先于所有规模条件；即使任务很多，只要不能从同一个起点独立完成，就必须选择轻量模式，不能混用并行 worktree 和顺序依赖两种执行方式。

## 阶段流程

**重要：每个 task/fix 完成后自动 commit。** 遵循"一个 task/fix 一个 commit"原则，commit 前必须执行编译检查且编译通过。全程不做自动 push 操作。

**断点检测（阶段流程入口）：**

从 `.codeforge-state.yaml` 读取 checkpoint，然后验证实际状态：

| checkpoint | 实际状态验证 | 路由到 |
|-----------|-------------|--------|
| `plan-generated-and-confirmed` | 计划文件有 checkbox 且全部未勾选 | Step 1（全新执行） |
| `plan-generated-and-confirmed` | 计划文件有 checkbox 且部分已勾选 | Step 1（断点恢复，从第一个未勾选继续） |
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
- 为每个任务创建专属 Git worktree，并在平台并发上限内并行分派实现者
- 每个任务在自己的 worktree 中完成实现、提交、独立审查和修复复审
- 子智能体不得修改共享计划和状态文件；worktree 审查通过不等于任务已完成
- 所有任务审查通过后，主会话按任务编号串行集成；每次集成后才更新该任务的 checkbox 和 checkpoint，并生成最终任务 commit
- 集成冲突、组合编译失败或 worktree 清理失败都必须显式阻塞

**轻量模式**：
在当前会话中直接执行：
- 按 `openspec/plans/` 下的计划文件逐个 Task 执行
- 严格遵循计划文件中每个 Step 的 checkbox 顺序
- 每个 Task 完成后执行收尾流程

**每个任务完成后的提交流程：**

完整模式由 `subagent-implement` 执行以下流程；轻量模式由当前会话直接执行：

1. **取得任务改动**：完整模式从已审查的任务 worktree 执行 `task-worktree integrate`；轻量模式使用当前工作树中的实现改动
2. **编译检查**：运行 `compile_command`，编译必须通过（如果 compile_command 为 null 则跳过）
3. **更新 checkbox**：用 Edit 工具将计划文件中**该 Task 下的所有** `- [ ]` 改为 `- [x]`（包括 Verify、Commit 等非实现步骤，不能遗漏）
4. **更新状态文件**：更新 `.codeforge-state.yaml` 的 `checkpoint: task-N-complete`
5. **自动 commit**：将代码改动 + 计划文件变更 + 状态文件变更一起提交到本地仓库
   - commit message 格式：`<类型>(<范围>): <task描述>`
   - 一个 task 对应一个 commit（包含计划文件和状态文件更新）
   - **全程不做 push 操作**
6. **记录集成**：完整模式运行 `task-worktree record PLAN_FILE N HEAD`；轻量模式跳过

**原子性保证**：先取得代码改动，再更新 checkbox 和状态文件，最后一起 commit。完整模式如果在 `integrate` 后、commit 前中断，主工作树会保留暂存改动；恢复时核对差异后继续编译和提交，不得重复集成。如果 commit 后、`record` 前中断，直接补记集成提交。如果 commit 和记录均完成，checkpoint、checkbox 和 worktree 清单共同证明该任务已完成。

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
2. **状态文件过期**：如果 checkpoint 声称某个 task 完成，但实际 checkbox 未勾选，回退到上一个确认一致的 checkpoint
3. **完整模式 worktree 状态**：同时读取 worktree 清单和进度账本；已审查但未集成的任务从串行集成继续，已提交但未记录的任务补跑 `record`
4. **环境检查**：断点恢复时跳过环境检查（已在首次运行时验证），直接进入执行

## 审查循环

如果审查者打回某个任务：
1. 实现者根据反馈修改
2. 重新提交审查
3. 循环直到通过

如果同一任务修改 3 次以上仍不通过，提示用户：「这个任务反复审查不通过，可能需要回到 propose 阶段重新审视设计方案。」

## 硬门

本阶段**禁止修改规格设计文档**（openspec/changes/ 下的 proposal.md、design.md、specs/）。如果实现过程中发现规格有问题，记录下来留到 archive 阶段处理。

**例外：** `tasks.md` 中的任务完成状态可在 Step 4 同步更新（仅限状态标记，不修改任务内容）。

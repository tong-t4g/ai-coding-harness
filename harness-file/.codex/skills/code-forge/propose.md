# CodeForge:propose — 规格阶段

## 目标

把用户的需求从模糊想法变成可执行的任务清单。通过项目感知 + 调用 skill 产出完整的规格文档和实现计划。

## 前置检查

检查项目根目录是否有 `openspec/`。没有则执行 `npx @fission-ai/openspec init`，然后再次检查；生成配置和 slash commands 属于正常副作用。初始化失败或目录仍不存在时返回 `BLOCKED`。

## 阶段流程

### 1. 项目分析（仅首次运行）

如果 `.codeforge-state.yaml` 不存在或 `project_profile` 为空，按以下确定性规则执行项目分析器：

| 检测项 | 检测方式 | 默认值 |
|---|---|---|
| **languages** | 统计 `src/`、`lib/`、`app/` 等源码目录下的文件扩展名，取占比最高的 1-2 种 | `[]` |
| **language_versions** | 按语言名记录项目声明或锁定的版本；优先读取项目文件（Java：`pom.xml`/`build.gradle*` 的 release/source/target，Go：`go.mod` 的 `go`，Rust：`Cargo.toml` 的 `rust-version`，Python：`pyproject.toml` 的 `requires-python`，Node.js：`.nvmrc`/`package.json.engines.node`），无法确定时为 `unknown`，禁止用本机版本猜测 | `{}` |
| **frameworks** | 读取 `package.json` 的 dependencies/devDependencies、`pom.xml` 的 `<dependencies>`、`go.mod` 的 require 等提取关键框架名 | `[]` |
| **framework_versions** | 按框架名记录依赖声明或锁定文件中的版本；优先使用 lockfile 或构建文件中的有效版本，Maven 属性/BOM 等无法解析时为 `unknown`，禁止用本机缓存版本猜测 | `{}` |
| **build_tool** | `pom.xml` → maven；`build.gradle`/`build.gradle.kts` → gradle；`package.json` → 根据 lock 文件选择 npm/yarn/pnpm；`go.mod` → go；`Cargo.toml` → cargo；`pyproject.toml` → python | `unknown` |
| **compile_command** | 根据下方构建命令映射推导 | `null` |
| **compile_scope** | 默认全量编译；只有下方 scoped 降级验证通过后才改为 `scoped` | `full` |
| **test_command** | 根据构建工具和测试目录推导 | `null` |
| **structure** | 存在 `modules/`、`packages/`、多个 `pom.xml` 或 `go.work` 时为 `monorepo`，否则为 `single-module` | `single-module` |
| **has_ci** | 检查 `.github/workflows/`、`.gitlab-ci.yml`、`Jenkinsfile`、`azure-pipelines.yml` 等 | `false` |

分析完成后将 `project_profile` 写入 `.codeforge-state.yaml`，并更新 `phase: propose`、`checkpoint: profiler-done`。

**构建命令映射：**

| build_tool | compile_command（默认） | test_command（默认） |
|---|---|---|
| maven | `mvn compile` | `mvn test` |
| gradle | `./gradlew compileJava` | `./gradlew test` |
| npm | `npm run build`（如果 script 存在） | `npm test`（如果 script 存在） |
| yarn | `yarn build`（如果 script 存在） | `yarn test`（如果 script 存在） |
| pnpm | `pnpm run build`（如果 script 存在） | `pnpm test`（如果 script 存在） |
| go | `go build ./...` | `go test ./...` |
| cargo | `cargo build` | `cargo test` |
| python | `null`（跳过编译） | `pytest`（如果安装了） |
| unknown | `null` | `null` |

**命令运行时验证：**

1. 执行前检查项目特有参数：Maven 根目录有 `settings.xml` 时附加 `-gs ./settings.xml`；Gradle 检查 `gradle.properties` 或 `local.properties`；npm、yarn、pnpm 检查 `.npmrc` 和对应 lock 文件。
2. 实际运行推导出的 compile_command（非 null 时）。成功则写入 project_profile，并保持 `compile_scope: full`。
3. 环境问题导致失败时，若 monorepo 的失败来自无关模块，尝试受影响模块的 scoped 编译（Maven：`mvn compile -pl <变更涉及模块> -am`；Gradle：`./gradlew :<模块>:compileJava`）。通过后把 `project_profile.compile_command` 改为已验证的 scoped 命令，并写入 `compile_scope: scoped`；apply 及后续任何构建验证都必须使用该命令，不得重新运行已知会因无关模块失败的全量命令。scoped 仍失败则返回 `BLOCKED`，等待用户提供正确命令。
4. 已有代码错误导致失败时，记录命令可用，把代码错误留到 apply 阶段。
5. test_command 不强制执行，但要确认测试框架已安装，例如检查 `pytest` 是否可用或检查 `package.json` 的 devDependencies。

**空白项目（greenfield）处理：**
如果是空项目（无源码、无配置），跳过分析，project_profile 保持默认空值。在需求确认步骤中一并确定技术栈（语言、框架、构建工具；若能确认版本也一并确认），分析完成后补充 project_profile。

### 2. 需求确认（这一环节是我觉得是最该重视的环节）

围绕用户需求的每个方面持续追问用户，直至双方达成一致理解。每次需要用户答案时，按“阶段 Agent 接口”返回 `NEEDS_USER` 并停止；Coordinator 回传答案后再继续。规则：

- 每次只问一个问题，等待用户反馈后再继续
- 每提出一个问题，都给出你推荐的答案
- 如果某项*事实*可以通过检查环境（文件系统、工具等）查明，就自行查找，不要询问用户。但*决策*必须由用户作出：逐项请用户决定，并等待回答
- 关注：目的、约束、成功标准
- 从用户描述中提取变更名（英文短横线格式，如 `add-user-auth`）

在用户确认双方已经达成共同理解之前，不要匆忙进入下一步。

**空白项目（greenfield）额外确认：**
如果 Step 1 中检测到是空项目（project_profile 为空），在此步骤中一并确认技术栈（语言、框架、构建工具）。确认后补充 `project_profile` 并更新 `.codeforge-state.yaml`。

**如果用户提供了需求链接（如 JIRA 任务、GitHub Issue）：**
先用 web reader 或其他方式获取需求详情，将完整需求作为本次需求的输入。

**自主模式：**
如果用户声明了自主执行意图（如「完全自主」「你决定」「不用确认」），跳过交互式需求确认，直接根据用户最初的需求描述进入 Step 3。空白项目自主模式下根据需求描述推断技术栈。

需求确认完成后，更新 `.codeforge-state.yaml`：`active_change: <变更名>`、`checkpoint: requirements-confirmed`。

### 3. 调用 openspec-propose 生成规格文档

调用原生 `openspec-propose` skill，通过 CLI 创建变更并生成所有 artifacts。

**做法：**

1. 宣布："调用 openspec-propose 生成规格文档"
2. 使用 Skill 工具调用 `openspec-propose`，args 格式：
   ```
   Change name: <变更名>. Description: [项目: {project_profile.languages} + {project_profile.frameworks}, 版本: {project_profile.language_versions} + {project_profile.framework_versions}, 构建: {project_profile.build_tool}] <需求描述>
   ```
   将 project_profile 信息作为上下文前缀附加到描述中，让 openspec-propose 能生成贴合项目技术栈的规格文档。
3. `openspec-propose` 会自动执行：
   - `openspec new change "<name>"` — 创建变更目录
   - `openspec status --change "<name>" --json` — 获取 artifact build order
   - 循环 `openspec instructions <artifact>` — 按依赖顺序生成每个 artifact
   - 产出：proposal.md、design.md、specs/、tasks.md
4. 等待 skill 完成后，验证 `openspec/changes/<变更名>/` 下所有 artifacts 已生成且**非空**（检查每个文件 size > 0）。如果某个 artifact 文件为空或不存在，重新调用 openspec-propose 补充缺失的 artifact。
5. **覆盖 openspec-propose 的执行建议**：openspec-propose 完成后会建议 "Run /opsx:apply"。在 CodeForge 上下文中忽略此建议，宣布 "回到 CodeForge 流程，继续生成实现计划"

**降级方案：** 如果 `openspec-propose` skill 不可用（Skill 工具返回 "Unknown skill"），手动执行等效操作：
1. 运行 `npx @fission-ai/openspec new change "<变更名>"` 创建变更目录
2. 运行 `npx @fission-ai/openspec status --change "<变更名>" --json` 获取 artifact build order
3. 对每个 artifact，运行 `npx @fission-ai/openspec instructions <artifact>` 获取生成指令
4. 按照指令内容，使用 Write 工具直接创建对应的 artifact 文件（proposal.md、design.md、specs/ 下的 .md 文件、tasks.md）
5. 确保每个 artifact 文件非空且内容完整

完成后更新 `.codeforge-state.yaml`：`checkpoint: openspec-generated`。

### 4. 调用 plans 生成实现计划

调用 `plans` skill，传入 openspec artifacts + project_profile 作为上下文。

**做法：**

1. 宣布："调用 plans 生成实现计划"
2. **准备上下文**：读取以下文件并构造上下文字符串：
   - `openspec/changes/<变更名>/proposal.md` — 需求背景和目标
   - `openspec/changes/<变更名>/design.md` — 技术方案
   - `openspec/changes/<变更名>/specs/` — 规格增量（所有 .md 文件）
   - `openspec/changes/<变更名>/tasks.md` — 任务清单（**作为权威任务分解，plans 应基于此展开**）
3. **准备 API 验证上下文**：提取关键框架 API 的实际签名，作为 plans 的额外约束。重点关注：
   - 框架提供的工具方法是否存在多个重载（参数个数/类型不同），确认计划中应使用哪个签名
   - 第三方库的 import / require 路径是否与直觉不同（如包名重组后的新路径）
   - 构建工具在项目实际环境中的可用命令（如私有仓库可能限制增量编译，必须全量编译）
   - 将验证结果整理为"框架 API 注意事项"列表，附加到 plans 的 args 中
4. 使用 Skill 工具调用 `plans`，args 传入上下文：
   ```
   变更名: <name>
   项目技术栈: {project_profile.languages} + {project_profile.frameworks}
   语言版本: {project_profile.language_versions}
   框架版本: {project_profile.framework_versions}
   构建工具: {project_profile.build_tool}
   测试框架: {project_profile.test_command}
   项目结构: {project_profile.structure}
   编译命令: {project_profile.compile_command}
   计划保存路径: openspec/plans/YYYY-MM-DD-<变更名>.md
   编译约束:
   - 本项目的编译命令为 {compile_command}，计划中每个 Task 完成后必须使用此命令验证编译
   - 接口层和实现层分开定义在不同的 Task 中会导致单独编译失败，必须在同一 Task 中同时修改接口和实现
   checkbox 唯一性约束:
   - 计划中每个 Step 的 checkbox 描述必须全局唯一，不能仅靠步骤编号区分（如"Step 2: 编译验证"会在多个 Task 中重复）
   - 推荐格式：`- [ ] **Step N: <动作描述>（Task <编号>）**` 或在步骤描述中包含 Task 特有的上下文（如文件名、类名）
   - 这确保 apply 阶段使用 Edit 工具更新 checkbox 时，old_string 在文件中唯一匹配
   执行关系约束:
   - 按业务与测试意图拆分 Task，不得为了提高并行率而扭曲任务边界
   - 每个 Task 必须列全直接前置任务；没有则明确写“无”
   - 每个 Task 的关联文件必须覆盖全部新建、修改和测试文件；同一路径可如实出现在多个 Task 中
   框架 API 注意事项:
   <Step 3 中验证的实际 API 签名列表>
   openspec artifacts:
   <将上述文件内容拼接>
   ```
   将完整 project_profile 信息（包括语言/框架版本；`unknown` 必须保留）、编译约束、API 验证结果传入，让 plans skill 从一开始就生成正确的任务分解，避免事后合并。
5. plans 会读取上下文，生成实现计划（File Structure 表 + 带 checkbox 的 TDD 微步骤），保存到 `openspec/plans/YYYY-MM-DD-<变更名>.md`
6. 确认 `openspec/plans/` 下有计划文件且包含至少 1 个 checkbox。如果没有 checkbox，说明 plans 未能基于 tasks.md 展开步骤，需要重新执行并更明确地指定 "按 tasks.md 中的每个 Task 展开为 TDD 微步骤"。
7. **绑定变更名**：在计划文件开头添加一行注释 `<!-- codeforge change: <变更名> -->`，用于 SKILL.md 状态检测时确认计划文件与活跃变更的对应关系。
8. **计划质量审查（必须完成）**：逐项检查 plans 生成的计划，确认以下维度全部通过。此步骤不可跳过，即使自主模式也必须执行：
   - **编译约束遵守**：接口+实现是否在同一 Task 中。如果 plans 仍将接口和实现拆分为不同 Task，手动合并并标注原因
   - **import 语句正确性**：检查计划中代码块的 import 语句是否与项目实际路径一致（对比 Step 3 中扫描的已有代码的 import 路径）
   - **无效代码检查**：检查代码块中是否有调试残留、空行占位、无意义的方法调用（如 `.getClass()` 仅用于触发泛型推断）
   - **类型一致性**：计划中后出现的 Task 引用的类型、方法签名是否与前面 Task 定义的一致
   - **执行关系完整性**：每个 Task 是否列全直接前置任务，输入依赖是否一致，是否不存在依赖环
   - **文件所有权完整性**：每个 Task 的关联文件是否覆盖全部预计改动；共享路径是否在所有相关 Task 中如实列出
   - 如果发现问题，直接在计划文件中修复，修复后重新确认编译依赖
9. **立即更新 checkpoint**：plans 完成且 Step 7-9 验证通过后，**立即**更新 `.codeforge-state.yaml`：`checkpoint: plan-generated`。这一步**不可跳过**，即使用户声明自主模式也必须先写 `plan-generated`，再在 Step 5(用户确认) 中更新为 `plan-generated-and-confirmed`。确保每个 checkpoint 都是原子性推进，避免中断时状态文件与实际文件不一致。

### 5. 用户确认

非自主模式通过 `CODEFORGE_RESULT.report` 展示产出摘要，并返回 `NEEDS_USER` 请用户确认「规格 OK，可以开始实现」：

- 变更名和位置
- 项目 profile 信息（语言、框架、版本、构建工具）
- 生成的 artifacts 列表
- 实现计划中的 Task 数量和关键步骤
- 预计涉及修改的文件列表

**修改回流规则：**
如果用户在本步骤提出任何需求修改，视为尚未达成共同理解，必须返回 Step 2 重新确认需求；确认后重新执行 Step 3 和 Step 4，重新生成 `proposal.md`、`design.md`、`specs/`、`tasks.md` 以及实现计划，旧 artifacts 和旧计划不得直接沿用进入 apply。

## 出口条件

- `openspec/changes/<变更名>/` 下有完整的 artifacts（由 openspec-propose 生成）
- `openspec/plans/` 下有对应的实现计划文件（由 plans 生成）
- 计划文件中至少有 1 个 checkbox
- 用户明确确认可以进入构建阶段，或用户已声明自主执行模式

用户确认后更新 `.codeforge-state.yaml`：`phase: apply`、`checkpoint: plan-generated-and-confirmed`，再返回 `DONE`；自主执行模式在满足全部出口条件后直接更新并返回 `DONE`。`report` 至少包含变更名、artifacts、Task 数量和预计修改文件。

## 断点恢复

重新运行时，先读取 `.codeforge-state.yaml` 的 checkpoint，然后检查实际文件状态：

| checkpoint | 实际文件状态 | 恢复到         |
|-----------|-------------|-------------|
| `profiler-done` | 无活跃变更目录 | Step 2（需求确认） |
| `requirements-confirmed` | 变更目录不存在 | Step 3（调用 openspec-propose skill） |
| `requirements-confirmed` | 变更目录存在但 artifacts 不完整或有空文件 | Step 3（openspec-propose 会自动补充） |
| `openspec-generated` | artifacts 完整但 `openspec/plans/` 无计划文件 | Step 4（调用 plans） |
| `plan-generated` | 计划文件存在但无 checkbox | Step 4（重新调用 plans） |
| `plan-generated` | 计划文件存在且有 checkbox | Step 5（用户确认） |
| `plan-generated-and-confirmed` | 计划文件存在且有 checkbox | 出口到 apply 阶段（`phase: apply, checkpoint: plan-generated-and-confirmed`） |
| `plan-generated-and-confirmed` | 计划文件不存在或无 checkbox | 回退到 Step 4（重新生成计划） |

**状态文件缺失时的降级**：如果没有 `.codeforge-state.yaml`，按实际文件扫描恢复：完整 artifacts + 有效计划但没有可验证的用户确认凭据时恢复到 Step 5；缺少 artifacts 或计划时恢复到对应生成步骤；只有确认凭据存在时才允许出口到 apply。不得仅凭计划存在推断用户已确认。

## 硬门

本阶段**禁止写任何代码或创建分支**。任何实现行为必须在 apply 阶段进行。

# AGENTS.md
- 此工程内的 bash、ts、js 脚本是要在 MacOS、Windows、Linux 多种环境中运行的，需确保能兼容。
- 此工程是一个为其它工程生成 skills 的项目，所以“harness-file”目录中的 AGENTS.md、skills、hooks 等文件无效，忽略它们，无需遵循。
- 也因为此工程是一个为其它工程生成 skills 的项目，所以“harness-file”目录中 skills、hooks 等文件不应只按照当前的环境来编写，而因该考虑不同操作系统的常规情况
- “harness-file\.codex”目录中的文件中的引用要注意以下，因为最终，skill 文件会安装在 $CODEX_HOME/skills/code-forge，Windows 上通常就是 %USERPROFILE%\.codex\skills\code-forge，macOS/Linux 上是 ~/.codex/skills/code-forge ，而 agents 和 hooks、config.toml 会安装在项目仓库根目录
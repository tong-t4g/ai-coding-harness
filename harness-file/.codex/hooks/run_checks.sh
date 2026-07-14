#!/bin/bash
# 1. 获取当前所有被修改、新增或删除的文件列表
CHANGED_FILES=$(git status --porcelain | awk '{print $2}')
# 2. 如果没有文件变动（极少见情况），直接退出
if [ -z "$CHANGED_FILES" ]; then
 exit 0
fi
# 3. 检查是否*只*修改了文档文件
# 过滤掉 .md, .txt, .json 等不需要跑测试的文件后缀
NON_DOC_CHANGES=$(echo "$CHANGED_FILES" | grep -vE '\.(md|txt|csv|json)$')
# 4. 判断逻辑
if [ -z "$NON_DOC_CHANGES" ]; then
 # 如果过滤后为空，说明这次改动的全是文档
 echo "[Hook 拦截] 仅检测到文档变动，跳过单元测试和语法检查。"
 exit 0
else
 # 只要包含哪怕一个非文档文件（比如 .py 或 .java），就老老实实跑测试
 echo "[Hook 触发] 检测到代码变动，开始执行全量检查..."
 # 下面放你原本的测试命令，比如：
 # pytest tests/

set -euo pipefail
echo "[hook] 开始执行编译检查..."
mvn -q -DskipTests compile
echo "[hook] 开始执行单元测试..."
mvn test
echo "[hook] 开始执行打包检查..."
mvn -DskipTests package
fi
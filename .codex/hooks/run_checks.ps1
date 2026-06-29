Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$changedFiles = git status --porcelain | ForEach-Object {
    ($_ -split '\s+', 2)[1]
} | Where-Object { $_ }

if (-not $changedFiles) {
    exit 0
}

$nonDocChanges = $changedFiles | Where-Object {
    $_ -notmatch '\.(md|txt|csv|json)$'
}

if (-not $nonDocChanges) {
    Write-Output "[Hook 拦截] 仅检测到文档变动，跳过单元测试和语法检查。"
    exit 0
}

Write-Output "[Hook 触发] 检测到代码变动，开始执行全量检查..."
Write-Output "[hook] 开始执行编译检查..."
mvn -q -DskipTests compile
Write-Output "[hook] 开始执行单元测试..."
mvn test
Write-Output "[hook] 开始执行打包检查..."
mvn -DskipTests package

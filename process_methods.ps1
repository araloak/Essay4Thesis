# 定义目标目录变量（方法或实验）
$targetFolder = "实验"  # 可修改为 "实验" 以切换目标目录
$essayFolder = "exps"  # 可修改为 "exps" 以切换对应的 essay 目录

# 定义目标目录路径
$baseDir = "data/thesis/第三章"
$targetDir = Join-Path -Path $baseDir -ChildPath $targetFolder

# 定义 Python 脚本路径
$scriptPath = "critic_and_improve.py"

# 遍历目标目录下的所有子文件夹
Get-ChildItem -Path $targetDir -Directory | ForEach-Object {
    $subDir = $_.FullName
    $bestFile = Join-Path -Path $subDir -ChildPath "候选qwen3.txt"

    # 检查最佳.txt 是否存在
    if (Test-Path $bestFile) {
        Write-Host "Processing file: $bestFile"

        # 定义其他必要的输入文件路径
        $essayFile = "data/essays/essay1/" + $essayFolder + "/" + ($_.Name) + ".txt"
        $draftPrompt = "prompts/essay4thesis_方法_prompt.txt"
        $draftExample = "data/thesis/example_essay4thesis_"+$targetFolder+".txt"
        $essay4thesisAbs = "data/thesis/第三章/前言/最佳.txt"

        # 调用 Python 脚本
        python $scriptPath --draft $bestFile --essay $essayFile --draft_prompt $draftPrompt --draft_example $draftExample --essay4thesis_abs $essay4thesisAbs --rounds 3 --model dsr1
    } else {
        Write-Host "最佳.txt not found in $subDir"
    }
}
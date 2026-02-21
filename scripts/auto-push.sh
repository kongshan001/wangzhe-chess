#!/bin/bash
# 王者之奕 - 自动提交和推送脚本

cd ~/clawd/wangzhe-chess

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

# 获取当前时间
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 统计变更
CHANGED_FILES=$(git diff --name-only | wc -l)
NEW_FILES=$(git ls-files --others --exclude-standard | wc -l)

echo "=== Auto Commit ==="
echo "Time: $TIMESTAMP"
echo "Changed: $CHANGED_FILES files"
echo "New: $NEW_FILES files"

# 添加所有文件
git add -A

# 生成提交信息
COMMIT_MSG="auto: 团队协作更新 ($TIMESTAMP)

变更统计:
- 修改文件: $CHANGED_FILES
- 新增文件: $NEW_FILES"

# 提交
git commit -m "$COMMIT_MSG"

# 推送
git push origin main

echo "=== Push Complete ==="

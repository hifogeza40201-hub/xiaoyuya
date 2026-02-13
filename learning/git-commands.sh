#!/bin/bash
################################################################################
# Git 常用命令脚本合集
# 文件名: git-commands.sh
# 说明: 将常用Git操作封装为快捷函数，方便日常使用
# 使用方法: source git-commands.sh
################################################################################

# ==================== 基础操作快捷函数 ====================

# 快速初始化并配置仓库
git-init() {
    local repo_name=$1
    if [ -z "$repo_name" ]; then
        echo "❌ 用法: git-init <仓库名>"
        return 1
    fi
    
    mkdir -p "$repo_name" && cd "$repo_name"
    git init
    echo "# $repo_name" > README.md
    git add README.md
    git commit -m "feat: 初始化仓库"
    echo "✅ 仓库 '$repo_name' 初始化完成"
}

# 快速提交（自动add）
git-quick() {
    local message=$1
    if [ -z "$message" ]; then
        echo "❌ 用法: git-quick <提交信息>"
        return 1
    fi
    
    git add .
    git commit -m "$message"
    echo "✅ 提交完成: $message"
}

# 快速推送当前分支
git-push-current() {
    local branch=$(git branch --show-current)
    git push -u origin "$branch"
    echo "✅ 已推送到 origin/$branch"
}

# ==================== 分支操作快捷函数 ====================

# 创建并切换到功能分支
git-feature() {
    local feature_name=$1
    if [ -z "$feature_name" ]; then
        echo "❌ 用法: git-feature <功能名>"
        return 1
    fi
    
    git checkout -b "feature/$feature_name"
    echo "✅ 已创建并切换到分支: feature/$feature_name"
}

# 创建并切换到修复分支
git-hotfix() {
    local fix_name=$1
    if [ -z "$fix_name" ]; then
        echo "❌ 用法: git-hotfix <修复名>"
        return 1
    fi
    
    git checkout main || git checkout master
    git pull
    git checkout -b "hotfix/$fix_name"
    echo "✅ 已创建并切换到分支: hotfix/$fix_name"
}

# 快速切换到主分支并更新
git-home() {
    local main_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
    git checkout "$main_branch" 2>/dev/null || git checkout master 2>/dev/null || git checkout main
    git pull origin $(git branch --show-current)
    echo "✅ 已回到主分支并更新"
}

# 安全删除分支（已合并）
git-rm-branch() {
    local branch=$1
    if [ -z "$branch" ]; then
        echo "❌ 用法: git-rm-branch <分支名>"
        return 1
    fi
    
    git branch -d "$branch"
    git push origin --delete "$branch" 2>/dev/null || echo "⚠️ 远程分支可能不存在"
    echo "✅ 分支 '$branch' 已删除"
}

# 列出所有分支（带描述）
git-branches() {
    echo "🌿 本地分支:"
    git branch -v
    echo ""
    echo "🌐 远程分支:"
    git branch -r -v
}

# ==================== 信息查看快捷函数 ====================

# 简洁状态查看
git-st() {
    echo "📊 Git 状态:"
    git status -s
    echo ""
    echo "📋 最近提交:"
    git log --oneline -5
}

# 图形化历史查看
git-log-graph() {
    git log --graph --oneline --all --decorate -20
}

# 查看本次修改详情
git-changes() {
    echo "📝 未暂存的修改:"
    git diff
    echo ""
    echo "📦 已暂存的修改:"
    git diff --staged
}

# ==================== 撤销操作快捷函数 ====================

# 撤销所有未提交的修改（慎用！）
git-undo-all() {
    read -p "⚠️ 确定要放弃所有未提交的修改吗？(y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        git checkout -- .
        git clean -fd
        echo "✅ 所有修改已放弃"
    else
        echo "❌ 操作已取消"
    fi
}

# 撤销最后一次提交（保留修改）
git-undo-commit() {
    git reset --soft HEAD~1
    echo "✅ 最后一次提交已撤销，修改保留在暂存区"
}

# 修改最后一次提交
git-fix() {
    local message=$1
    if [ -z "$message" ]; then
        git commit --amend --no-edit
        echo "✅ 已将当前修改合并到最后一次提交"
    else
        git commit --amend -m "$message"
        echo "✅ 已修改最后一次提交: $message"
    fi
}

# ==================== 高级工作流快捷函数 ====================

# 同步主分支并rebase当前分支
git-sync() {
    local current=$(git branch --show-current)
    local main_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
    
    git fetch origin
    git rebase origin/"$main_branch"
    echo "✅ 当前分支已rebase到最新 $main_branch"
}

# 快速创建PR分支并推送
git-pr() {
    local current=$(git branch --show-current)
    git push -u origin "$current"
    echo "✅ 分支 '$current' 已推送，请在GitHub/GitLab创建PR"
}

# 清理已合并的远程分支引用
git-cleanup() {
    git remote prune origin
    echo "✅ 已清理远程分支引用"
    
    echo ""
    echo "🧹 已合并的本地分支:"
    git branch --merged | grep -v "\*" | grep -v "main\|master"
}

# ==================== 实用工具函数 ====================

# 查看某个文件的所有修改历史
git-file-history() {
    local file=$1
    if [ -z "$file" ]; then
        echo "❌ 用法: git-file-history <文件名>"
        return 1
    fi
    git log --follow -p -- "$file"
}

# 搜索提交历史中的关键字
git-search() {
    local keyword=$1
    if [ -z "$keyword" ]; then
        echo "❌ 用法: git-search <关键字>"
        return 1
    fi
    git log --all --grep="$keyword" --oneline
    git log --all -S "$keyword" --oneline
}

# 显示当前仓库统计信息
git-stats() {
    echo "📊 仓库统计:"
    echo "提交总数: $(git rev-list --all --count)"
    echo "分支数量: $(git branch -a | wc -l)"
    echo "贡献者数量: $(git log --format='%an' | sort -u | wc -l)"
    echo ""
    echo "🔥 最活跃贡献者:"
    git log --format='%an' | sort | uniq -c | sort -rn | head -5
}

# 备份当前工作区（WIP提交）
git-backup() {
    git add .
    git commit -m "WIP: $(date '+%Y-%m-%d %H:%M:%S') 备份"
    echo "✅ 工作区已备份"
}

# 恢复WIP备份（撤销最后一次提交，保留修改）
git-restore() {
    git reset --soft HEAD~1
    echo "✅ 已恢复备份到工作区"
}

# ==================== 帮助信息 ====================

git-help-commands() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║                     🚀 Git 快捷命令脚本帮助                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 基础操作                                                                  ║
║   git-init <名>          快速初始化新仓库                                 ║
║   git-quick <消息>       快速add+commit                                   ║
║   git-push-current       推送当前分支                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 分支操作                                                                  ║
║   git-feature <名>       创建功能分支                                     ║
║   git-hotfix <名>        创建修复分支                                     ║
║   git-home               回到主分支并更新                                 ║
║   git-rm-branch <名>     删除本地和远程分支                               ║
║   git-branches           查看所有分支                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 信息查看                                                                  ║
║   git-st                 简洁状态                                         ║
║   git-log-graph          图形化历史                                       ║
║   git-changes            查看修改详情                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 撤销操作                                                                  ║
║   git-undo-all           放弃所有未提交修改                               ║
║   git-undo-commit        撤销最后一次提交                                 ║
║   git-fix [消息]         修改最后一次提交                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 高级操作                                                                  ║
║   git-sync               同步并rebase                                     ║
║   git-pr                 推送当前分支用于PR                               ║
║   git-cleanup            清理已合并分支                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 工具函数                                                                  ║
║   git-file-history <文件> 查看文件历史                                    ║
║   git-search <关键字>    搜索提交历史                                     ║
║   git-stats              仓库统计                                         ║
║   git-backup             备份工作区                                       ║
║   git-restore            恢复备份                                         ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
}

echo "🚀 Git快捷命令脚本已加载！运行 git-help-commands 查看帮助"

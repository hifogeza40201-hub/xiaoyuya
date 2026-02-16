#!/bin/bash
#
# 消息检索脚本
# 基于 ripgrep + fzf 的快速检索
#

WORKSPACE_DIR="${WORKSPACE_DIR:-C:\\Users\\Admin\\.openclaw\\workspace}"
CHAT_STREAM_DIR="$WORKSPACE_DIR/memory/chat-stream"
SQLITE_DB="$WORKSPACE_DIR/memory/chat-stream/index.sqlite"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [QUERY]

消息检索工具 - 快速搜索历史消息

Options:
    -p, --platform PLATFORM    指定平台 (telegram|dingtalk|all)
    -d, --date DATE           指定日期 (YYYY-MM-DD 或 YYYY-MM)
    -t, --tag TAG             按标签搜索
    -s, --sender NAME         按发送者搜索
    -l, --limit N             限制结果数量 (默认 50)
    -f, --fzf                 使用 fzf 交互式搜索
    -h, --help                显示帮助

Examples:
    $(basename "$0") "备份方案"                           # 搜索关键词
    $(basename "$0") -p telegram "学习轮次"              # 指定平台
    $(basename "$0") -d 2026-02 "早安"                   # 指定月份
    $(basename "$0") -t "#待办"                          # 搜索标签
    $(basename "$0") -s "小宇" "任务"                    # 指定发送者
    $(basename "$0") -f                                   # 交互式搜索
EOF
}

# 解析参数
PLATFORM=""
DATE=""
TAG=""
SENDER=""
LIMIT=50
USE_FZF=false
QUERY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -s|--sender)
            SENDER="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -f|--fzf)
            USE_FZF=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

# 检查依赖
check_deps() {
    if ! command -v rg &> /dev/null; then
        echo -e "${RED}Error: ripgrep (rg) not found${NC}"
        echo "Install: https://github.com/BurntSushi/ripgrep"
        exit 1
    fi
    
    if [ "$USE_FZF" = true ] && ! command -v fzf &> /dev/null; then
        echo -e "${YELLOW}Warning: fzf not found, falling back to normal search${NC}"
        USE_FZF=false
    fi
}

# 构建搜索范围
build_search_scope() {
    local scope=""
    
    if [ -n "$DATE" ]; then
        # 指定日期或月份
        if [ -f "$CHAT_STREAM_DIR/${DATE}.jsonl" ]; then
            scope="$CHAT_STREAM_DIR/${DATE}.jsonl"
        else
            # 按月份匹配
            scope=$(find "$CHAT_STREAM_DIR" -name "${DATE}*.jsonl" -type f 2>/dev/null | tr '\n' ' ')
        fi
    else
        # 搜索所有文件
        scope="$CHAT_STREAM_DIR"
    fi
    
    echo "$scope"
}

# 格式化输出
format_message() {
    local line="$1"
    local msg_id=$(echo "$line" | jq -r '.msg_id // "unknown"')
    local platform=$(echo "$line" | jq -r '.platform // "unknown"')
    local sender=$(echo "$line" | jq -r '.sender.name // "unknown"')
    local timestamp=$(echo "$line" | jq -r '.timestamp // ""')
    local body=$(echo "$line" | jq -r '.content.body // ""' | head -c 100)
    local tags=$(echo "$line" | jq -r '.tags | join(", ") // ""')
    
    # 截断长消息
    if [ ${#body} -ge 100 ]; then
        body="${body}..."
    fi
    
    # 格式化时间
    local time="${timestamp:11:8}"
    [ -z "$time" ] && time="????"
    
    # 输出
    echo -e "${BLUE}[$time]${NC} ${GREEN}$sender${NC} @ ${YELLOW}$platform${NC}"
    echo "    $body"
    [ -n "$tags" ] && echo -e "    ${YELLOW}$tags${NC}"
    echo ""
}

# 普通搜索
do_search() {
    local scope=$(build_search_scope)
    local rg_args=""
    
    # 平台过滤
    if [ -n "$PLATFORM" ] && [ "$PLATFORM" != "all" ]; then
        rg_args="$rg_args --glob '*${PLATFORM}*'"
    fi
    
    # 执行搜索
    if [ -n "$QUERY" ]; then
        echo -e "${GREEN}Searching for: $QUERY${NC}"
        echo ""
        
        rg $rg_args -i "$QUERY" $scope --json -n | \
        jq -r 'select(.type == "match") | .data.lines.text' | \
        head -n "$LIMIT" | \
        while read -r line; do
            format_message "$line"
        done
    elif [ -n "$TAG" ]; then
        echo -e "${GREEN}Searching for tag: $TAG${NC}"
        echo ""
        
        rg $rg_args -i "\"$TAG\"" $scope --json -n | \
        jq -r 'select(.type == "match") | .data.lines.text' | \
        head -n "$LIMIT" | \
        while read -r line; do
            format_message "$line"
        done
    fi
}

# FZF交互式搜索
do_fzf_search() {
    local scope=$(build_search_scope)
    
    # 构建预览命令
    local preview_cmd="echo {} | jq -C '.' 2>/dev/null || echo {}"
    
    rg -i "" $scope --json | \
    jq -r 'select(.type == "match") | .data.lines.text' | \
    fzf --preview "$preview_cmd" \
        --preview-window=right:50%:wrap \
        --height=80% \
        --border \
        --prompt="Search messages: " \
        --header="Ctrl-C to cancel | Enter to view"
}

# SQLite搜索 (如果可用)
do_sqlite_search() {
    if [ ! -f "$SQLITE_DB" ]; then
        echo -e "${YELLOW}SQLite index not found, using file search${NC}"
        do_search
        return
    fi
    
    local sql="SELECT json_object(
        'msg_id', msg_id,
        'platform', platform,
        'sender', json_object('name', sender_name),
        'timestamp', timestamp,
        'content', json_object('body', content_body)
    ) FROM messages WHERE 1=1"
    
    if [ -n "$QUERY" ]; then
        sql="$sql AND content_body LIKE '%$QUERY%'"
    fi
    
    if [ -n "$PLATFORM" ] && [ "$PLATFORM" != "all" ]; then
        sql="$sql AND platform = '$PLATFORM'"
    fi
    
    if [ -n "$SENDER" ]; then
        sql="$sql AND sender_name LIKE '%$SENDER%'"
    fi
    
    sql="$sql ORDER BY timestamp DESC LIMIT $LIMIT"
    
    sqlite3 "$SQLITE_DB" "$sql" | while read -r line; do
        format_message "$line"
    done
}

# 主函数
main() {
    check_deps
    
    # 确保目录存在
    if [ ! -d "$CHAT_STREAM_DIR" ]; then
        echo -e "${YELLOW}Chat stream directory not found: $CHAT_STREAM_DIR${NC}"
        echo "Creating directory..."
        mkdir -p "$CHAT_STREAM_DIR"
    fi
    
    # 执行搜索
    if [ "$USE_FZF" = true ]; then
        do_fzf_search
    else
        do_search
    fi
}

main

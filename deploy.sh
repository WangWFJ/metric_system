#!/usr/bin/env bash
# =========================================================
# 企业级 Docker Compose 部署脚本
# 适用：FastAPI / 外部数据库 / Nginx
# 环境：Linux / WSL2 / Docker Desktop
# =========================================================

set -Eeuo pipefail

#######################################
# 基础信息
#######################################
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="$(basename "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

#######################################
# 子命令
#######################################
CMD="${1:-up}"

#######################################
# 日志函数
#######################################
log()  { echo -e "\033[1;32m[deploy]\033[0m $*"; }
warn() { echo -e "\033[1;33m[warn]\033[0m   $*" >&2; }
err()  { echo -e "\033[1;31m[error]\033[0m  $*" >&2; exit 1; }

#######################################
# 环境识别
#######################################
IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then
  IS_WSL=1
fi

#######################################
# 默认 .env
#######################################
DEFAULT_ENV_CONTENT='
# ================= Production .env =================

# Database
DATABASE_URL=mysql+aiomysql://user:password@db.example.com:3306/db_name?charset=utf8mb4

# Backend (FastAPI / Gunicorn)
BACKEND_PORT=8081
WORKERS=2
# APP_MODULE=app.main:app

# Frontend (Nginx)
FRONTEND_PORT=8080
FRONTEND_CONTAINER_PORT=80

# Docker build
USE_BUILDKIT=0
'

#######################################
# 生成 .env（幂等）
#######################################
if [[ ! -f .env ]]; then
  log "未检测到 .env，正在生成默认配置..."
  printf "%s\n" "$DEFAULT_ENV_CONTENT" > .env
  log "已生成 .env（请根据需要修改）"
fi

#######################################
# 修复 .env 首行异常
#######################################
first_line="$(head -n 1 .env | tr -d '\r')"
if [[ "$first_line" == "\\" ]]; then
  warn ".env 首行异常，已自动修复"
  printf "%s\n" "$DEFAULT_ENV_CONTENT" > .env
fi

#######################################
# 加载 .env
#######################################
set -a
# shellcheck disable=SC1091
source ./.env
set +a

#######################################
# BuildKit 控制
#######################################
if [[ "${USE_BUILDKIT:-0}" == "1" ]]; then
  export COMPOSE_DOCKER_CLI_BUILD=1
  export DOCKER_BUILDKIT=1
  log "已启用 BuildKit"
else
  export COMPOSE_DOCKER_CLI_BUILD=0
  export DOCKER_BUILDKIT=0
  log "已禁用 BuildKit（兼容优先）"
fi

#######################################
# 修复 WSL Docker Desktop credential helper
#######################################
ORIG_DOCKER_CONFIG="${DOCKER_CONFIG:-$HOME/.docker}"
ORIG_CONFIG="$ORIG_DOCKER_CONFIG/config.json"

if [[ $IS_WSL -eq 1 ]] && [[ -f "$ORIG_CONFIG" ]] \
   && grep -qi '"credsStore"[[:space:]]*:[[:space:]]*"desktop"' "$ORIG_CONFIG"; then

  TMP_DOCKER_CONFIG="$SCRIPT_DIR/.docker-config"
  mkdir -p "$TMP_DOCKER_CONFIG"
  printf '%s\n' '{}' > "$TMP_DOCKER_CONFIG/config.json"
  export DOCKER_CONFIG="$TMP_DOCKER_CONFIG"

  log "WSL 环境下已自动规避 Docker Desktop credential helper"
fi

#######################################
# 端口校验
#######################################
for p in "$FRONTEND_PORT" "$BACKEND_PORT"; do
  [[ "$p" == "8000" ]] && err "禁止使用宿主机 8000 端口（常被占用）"
done

#######################################
# 必要环境变量校验
#######################################
if [[ -z "${DATABASE_URL:-}" ]]; then
  err "缺少 DATABASE_URL，请在 .env 中配置外部数据库连接字符串"
fi

#######################################
# Docker 检查
#######################################
command -v docker >/dev/null 2>&1 || err "未安装 docker"
docker info >/dev/null 2>&1 || err "Docker 未启动或无权限"

#######################################
# 子命令实现
#######################################
case "$CMD" in
  up)
    log "启动服务（生产模式）..."
    docker compose --env-file ./.env up -d --build
    ;;
  down)
    log "停止并移除容器..."
    docker compose down
    ;;
  restart)
    log "重启服务..."
    docker compose restart
    ;;
  rebuild)
    log "强制重新构建并启动..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    ;;
  logs)
    SERVICE="${2:-}"
    if [[ -n "$SERVICE" ]]; then
      docker compose logs -f --tail=200 "$SERVICE"
    else
      docker compose logs -f --tail=200
    fi
    ;;
  ps)
    docker compose ps
    ;;
  *)
    err "未知命令：$CMD
用法：
  ./deploy.sh up
  ./deploy.sh down
  ./deploy.sh restart
  ./deploy.sh rebuild
  ./deploy.sh logs [service]
  ./deploy.sh ps"
    ;;
esac

#######################################
# 启动信息
#######################################
if [[ "$CMD" == "up" ]]; then
  echo
  log "部署完成："
  echo "- Backend : http://localhost:${BACKEND_PORT}"
  echo "- Frontend: http://localhost:${FRONTEND_PORT}"
  echo
  log "常用命令："
  echo "  ./deploy.sh ps"
  echo "  ./deploy.sh logs backend"
fi

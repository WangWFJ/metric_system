# 前端生产镜像：Node 构建 + Nginx 运行（多阶段）
# 自动识别 npm / yarn / pnpm，使用系统默认仓库构建

########## 构建阶段（Node） ##########
FROM node:24-alpine AS builder
WORKDIR /app
ENV NODE_ENV=production

# 复制前端源码（假设项目位于 ./frontend）
COPY frontend/ /app/

# 安装依赖并构建，自动识别包管理器与锁文件
RUN set -eux; \
  npm config set registry https://registry.npmmirror.com; \
  if [ -f /app/yarn.lock ]; then \
    yarn config set registry https://registry.npmmirror.com || true; \
    yarn install --frozen-lockfile; \
    yarn run build; \
  elif [ -f /app/pnpm-lock.yaml ]; then \
    npm install -g pnpm --registry=https://registry.npmmirror.com; \
    pnpm config set registry https://registry.npmmirror.com; \
    pnpm install --frozen-lockfile; \
    pnpm run build; \
  else \
    npm ci || npm install; \
    npm run build; \
  fi; \
  OUT_DIR=$( [ -d dist ] && echo dist || ([ -d build ] && echo build || echo dist) ); \
  mkdir -p /opt/build-output; \
  cp -r "$OUT_DIR"/* /opt/build-output/ || true

########## 运行阶段（Nginx） ##########
FROM nginx:alpine AS runtime

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && apk update && apk add --no-cache gettext

# 容器内部监听端口通过环境变量注入（默认 80）
ENV FRONTEND_CONTAINER_PORT=80
ENV BACKEND_PORT=8081

# 拷贝构建产物到 Nginx 静态目录
COPY --from=builder /opt/build-output /usr/share/nginx/html

# Nginx 模板：复制本地模板文件
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# 使用 envsubst 渲染模板并以前台模式运行 Nginx
# 注意：指定变量列表以避免替换 Nginx 内置变量（如 $uri）
CMD ["sh", "-c", "envsubst '${FRONTEND_CONTAINER_PORT} ${BACKEND_PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'" ]

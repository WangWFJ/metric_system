# ---------- build stage ----------
FROM node:20-alpine AS build
WORKDIR /app

# 1. 复制锁文件
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# 2. 预先启用并固定 pnpm（关键！）
RUN corepack enable \
 && corepack prepare pnpm@8.15.5 --activate \
 && npm config set registry https://registry.npmmirror.com

# 3. 根据锁文件安装依赖
RUN if [ -f package-lock.json ]; then \
      npm ci; \
    elif [ -f yarn.lock ]; then \
      yarn install --frozen-lockfile; \
    elif [ -f pnpm-lock.yaml ]; then \
      pnpm install --frozen-lockfile; \
    else \
      npm install; \
    fi

# 4. 拷贝源码并构建
COPY . .
RUN npm run build

# ---------- runtime stage ----------
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx","-g","daemon off;"]

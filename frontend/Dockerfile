FROM node:22.17.0

# 设置工作目录
WORKDIR /app

# 使用国内镜像加速依赖下载（可选）
RUN npm install -g pnpm && \
    npm config set registry https://registry.npmmirror.com

# 拷贝依赖描述文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖（使用缓存）
RUN pnpm install

# 拷贝源代码
COPY . .

# 构建项目（next.js）
RUN pnpm build

EXPOSE 3000

# 启动服务
CMD ["pnpm", "start"]


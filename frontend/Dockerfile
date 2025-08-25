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

# 注意：不复制源代码，因为部署时会通过挂载方式提供
# 这样可以实现代码热更新和实时同步

# 创建public目录，确保静态资源目录结构存在
RUN mkdir -p public

# 预先复制logo文件到public目录（作为备用）
# 实际运行时可能会被挂载的代码覆盖
COPY logo.jpg ./public/logo.jpg

EXPOSE 3000

# 启动服务
CMD ["pnpm", "start"]


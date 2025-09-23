# 使用官方Python镜像
FROM python:3.9-slim

# 设置工作目录为/doub
WORKDIR /doub

# 复制整个项目目录
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露Flask默认端口
EXPOSE 5000

# 设置环境变量（根据你的app.py调整）
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# 启动命令
CMD ["flask", "run", "--host=0.0.0.0"]


# 双均线策略系统 📈

一个基于Flask和前端技术的双均线交易策略分析系统，支持ETF数据分析和可视化展示。

## ✨ 功能特性

- 🔍 **ETF数据分析**: 支持多种ETF基金的历史数据获取和分析
- 📊 **双均线策略**: 实现经典的短期/长期移动平均线交叉策略
- 📈 **可视化图表**: 提供直观的价格走势和信号展示
- 🌐 **Web界面**: 现代化的响应式前端界面
- 🐳 **Docker支持**: 一键部署，开箱即用
- 🔄 **实时数据**: 集成Tushare API获取实时金融数据

## 🚀 快速开始

### 使用Docker部署（推荐）

1. **克隆项目**
   ```bash
   git clone https://github.com/eachonxian/XDoubleMA.git
   cd XDoubleMA
   ```

2. **克隆项目**
   在strategy_api.py中添加Tushare Token

3. **构建Docker镜像**
   ```bash
   docker build -t x-double-ma .
   ```

4. **运行容器**
   ```bash
   docker run -p 5000:5000 -e x-double-ma
   ```

5. **访问应用**
   
   打开浏览器访问: `http://localhost:5000`

### 本地开发部署

1. **环境要求**
   - Python 3.9+
   - pip

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **设置环境变量**
   ```bash
   export FLASK_APP=backend/app.py
   export FLASK_ENV=development
   ```

4. **启动应用**
   ```bash
   flask run --host=0.0.0.0
   ```

## 🏗️ 项目结构

```
doub/
├── backend/                 # 后端Flask应用
│   ├── app.py              # 主应用文件
│   └── strategy_api.py     # 策略API逻辑
├── frontend/               # 前端文件
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript文件
│   ├── index.html         # 主页面
│   └── strategy.html      # 策略分析页面
├── fund_code.csv          # ETF代码数据
├── Dockerfile             # Docker配置
├── requirements.txt       # Python依赖
└── README.md             # 项目文档
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `FLASK_ENV` | Flask运行环境 | production | 否 |
| `FLASK_APP` | Flask应用入口 | backend/app.py | 否 |

### Tushare Token获取

1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号并获取API Token
3. 设置环境变量或在代码中配置

## 📊 策略说明

### 双均线策略原理

- **短期均线**: 默认5日移动平均线
- **长期均线**: 默认20日移动平均线
- **买入信号**: 短期均线上穿长期均线（金叉）
- **卖出信号**: 短期均线下穿长期均线（死叉）

### 支持的数据源

- ETF基金数据
- 股票数据（备用）
- 前复权价格处理

## 🛠️ 开发指南

### 添加新策略

1. 在 `strategy_api.py` 中实现策略逻辑
2. 在前端添加对应的UI组件
3. 更新API接口文档

### 自定义ETF列表

编辑 `fund_code.csv` 文件，格式如下：
```csv
,ts_code,name
0,510300.SH,沪深300ETF
1,159919.SZ,沪深300ETF
```

## 🐛 故障排除

### 常见问题

1. **Tushare API调用失败**
   - 检查Token是否正确设置
   - 确认网络连接正常
   - 验证API调用次数限制

2. **Docker容器启动失败**
   - 检查端口5000是否被占用
   - 确认Docker服务正常运行

3. **前端页面无法加载**
   - 检查Flask应用是否正常启动
   - 确认CORS配置正确

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/doub/issues)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！


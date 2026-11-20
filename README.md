# HanboweiOJ

面向中国青少年信息学奥赛学习的教学型 Online Judge。首期面向内部学生与教师，使用 C++（GNU++17），以 2025 年修订版 NOI 大纲作为课程映射依据。

## 项目文档
- [产品需求](docs/PRODUCT_REQUIREMENTS.md)
- [技术架构](docs/ARCHITECTURE.md)
- [课程模型](docs/CURRICULUM_MODEL.md)
- [题目数据规范](docs/PROBLEM_FORMAT.md)
- [安全与隐私](docs/SAFETY_AND_PRIVACY.md)
- [开发路线图](docs/ROADMAP.md)

## 本地开发
1. 安装 Docker Desktop。
2. 复制 `.env.example` 为 `.env`，并修改本地数据库密码。
3. 在项目根目录运行 `docker compose up --build`。
4. 前端：http://localhost:3000；API 健康检查：http://localhost:8000/health；API 文档：http://localhost:8000/docs。

也可分别启动：前端目录执行 `npm install`、`npm run dev`；后端目录执行 `pip install -e '.[dev]'`、`uvicorn app.main:app --reload`。

## 当前状态
工程骨架阶段。尚未实现账号体系、课程内容、题库和安全 Runner；当前页面为开发占位页，不是生产服务。

## 安全原则
- 绝不在 Web/API 进程或宿主机 shell 中直接运行学生代码。
- 隐藏测试数据、标准答案和内部判题路径不得暴露给学生。
- 正式 Runner 必须独立隔离并通过安全评审。
- 不提交 `.env`、访问令牌、密码或私钥。

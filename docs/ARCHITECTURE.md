# HanboweiOJ 技术架构

- 文档版本：0.1
- 状态：首版设计；应用骨架落地前逐项形成 ADR

## 1. 总体结构

~~~text
Browser
  |
  v
Next.js Web
  |
  v
FastAPI API ---------------- PostgreSQL
  |                              |
  |                              +-- 用户、课程、题目、提交元数据
  |
  +---- Redis / Queue
            |
            v
       Judge Scheduler
            |
            v
       Isolated Judge Workers
            |
            +-- compiler sandbox
            +-- per-test execution sandbox
            +-- resource / output limits
            |
            v
       Result Processor ------ PostgreSQL
            |
            +---- Learning Analysis Service
                       |
                       +-- rules-based evidence
                       +-- optional AI explanation
~~~

浏览器、业务 API、调度器和运行学生代码的 Worker 必须分离。API 不执行学生提交的程序。

## 2. 建议技术

| 层 | 首版技术 | 说明 |
|---|---|---|
| Web | Next.js + TypeScript | 学习界面、题目页、编辑器、管理后台 |
| API | Python + FastAPI | 账号、课程、题库、提交、报告 |
| 数据库 | PostgreSQL | 事务性业务数据与关联关系 |
| 队列/缓存 | Redis | 评测任务排队、状态缓存、限流 |
| Judge | 独立 Worker | 编译与运行，独立扩缩容 |
| 隔离 | 一次性容器或更强隔离运行时 | 非特权、资源限制、默认无网络 |
| 交付 | Docker Compose + CI | 开发与测试环境；生产部署另行评估 |

此表是拟定方案，不代表依赖版本已经锁定。实施时选定稳定版本并提交 lockfile。

## 3. 服务边界

### Web
- 只调用公开 API。
- 不保存标准答案、隐藏数据或评测密钥。
- 编辑器提交代码时只传题目 ID、语言、代码和必要的幂等标识。

### API
- 执行身份认证、授权、输入校验、配额与限流。
- 创建 submission 并投递 job。
- 仅返回学生有权查看的评测信息。
- 不挂载判题数据目录，不拥有 Docker socket，不编译/执行提交代码。

### Judge Scheduler
- 从队列领取任务。
- 校验题目版本、语言版本和资源配置。
- 将任务派发给受限 Worker。
- Worker 结果需校验来源、任务 ID 和状态转换。

### Judge Worker
- 每个 submission/test run 使用隔离执行环境。
- 以非 root 身份运行；只读基础文件系统；临时工作目录；限制 CPU、内存、进程数、磁盘、输出量和墙钟时间。
- 默认禁用网络、特权模式、宿主目录挂载和宿主 Docker socket。
- 使用 seccomp、Linux namespaces/cgroups 等宿主能力；生产环境需安全审查，必要时采用 microVM 或专用沙箱。
- 评测输入、期望输出和内部配置放入仅 Worker 可读的隔离目录。
- 清理运行目录与进程，记录 Worker 镜像摘要和工具链版本。

## 4. 判题状态模型

~~~text
queued → compiling → running → judging → accepted / wrong_answer / time_limit_exceeded / memory_limit_exceeded / runtime_error / compilation_error / system_error
~~~

- system_error 不应被误标为学生错误。
- 评测重试需要幂等控制，防止重复计分或重复生成错题。
- 状态转换由服务端校验，不接受客户端直接修改。
- 首版可逐测试点记录 pass/fail 与资源统计；不向学生暴露隐藏输入、隐藏输出或标准答案。

## 5. 数据流
1. 学生发起提交。
2. API 校验身份、题目发布状态、语言、代码长度和提交频率。
3. API 写入 submission（queued）并投递队列消息。
4. Scheduler 派发到可用 Worker。
5. Worker 在受限环境编译，再按题目配置执行测试点。
6. Result Processor 校验、汇总结果并写入 submission。
7. 学习分析服务读取可用证据，生成错因候选和练习建议。
8. Web 查询提交结果和学习报告。

## 6. 可观测性
至少记录：
- submission_id、job_id、problem_version_id、worker_id。
- judge image digest、compiler version、编译参数。
- 任务创建/开始/完成时间、状态、退出码、耗时与内存。
- 系统异常、重试次数和取消原因。

日志不得记录不必要的个人信息、认证令牌或完整隐藏测试数据。

## 7. API 领域（初步）
- /api/v1/auth/*
- /api/v1/users/*
- /api/v1/curriculum/*
- /api/v1/lessons/*
- /api/v1/problems/*
- /api/v1/submissions/*
- /api/v1/learning/*
- /api/v1/teacher/*
- /api/v1/admin/*

API 采用版本前缀；公开 DTO 与数据库模型分离。

## 8. 架构演进
先用清晰的模块化单体 API + 单独 Judge Worker，避免初期过度微服务化。只有当评测吞吐、隔离边界或团队协作确实需要时，再拆分课程、分析等服务。

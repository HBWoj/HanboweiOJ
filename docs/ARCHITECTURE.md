# HanboweiOJ 技术架构
版本：v0.1｜状态：建议方案，技术评审后锁定

## 1. 架构原则
教学业务优先；Web/API 与不可信代码执行严格隔离；MVP 使用模块化单体 API 加独立判题服务；重要业务实体可追溯版本；关键操作可审计。

## 2. 建议技术栈
| 层次 | 建议 | 用途 |
|---|---|---|
| Web | Next.js + TypeScript | 学生、教师、管理端 |
| UI | Tailwind CSS | 统一界面 |
| API | Python FastAPI | REST API 与业务逻辑 |
| ORM/迁移 | SQLAlchemy 2 + Alembic | 数据访问与迁移 |
| 数据库 | PostgreSQL | 核心业务数据 |
| 队列/缓存 | Redis | 判题队列、缓存 |
| 后台任务 | Celery 或 RQ（二选一） | 异步任务 |
| 判题 | 独立 Judge Worker + Runner | 编译、运行、测试 |
| 文件 | 私有对象存储或受控磁盘 | 题目附件和测试数据 |
| 开发环境 | Docker Compose | 本地联调 |

以上是建议方案，编码前结合部署条件和团队熟悉度确定。

## 3. 逻辑组件
Web 前端；FastAPI API；PostgreSQL；Redis；Judge Worker；独立 Runner；私有文件存储；日志、指标、告警和审计。
后端领域模块：identity、classroom、curriculum、problem、submission、judge、assignment、learning、analytics、audit。首期在一个 FastAPI 项目内按领域分包，不必拆成多个微服务。

## 4. 判题流程
1. 学生提交代码，API 校验身份、题目状态和提交频率。
2. 保存 Submission，状态设为 Pending，并创建 JudgeJob。
3. 队列通知 Worker。
4. Worker 获取题目版本、编译配置和受控测试数据引用。
5. Runner 在隔离环境编译并逐组测试。
6. Worker 汇总状态、耗时和内存，写入结果。
7. API 只返回学生有权查看的安全结果。
状态流转：Pending → Queued → Running → Finished；最终结果映射 AC/WA/CE/RE/TLE/MLE/OLE/SE。任务需有幂等标识、超时回收和安全重试机制。

## 5. Runner 安全边界
用户代码是不可信程序，禁止在 Next.js、FastAPI 或普通后台任务进程直接执行。生产 Runner 应位于独立机器或虚拟机边界，并实施：
- 默认禁用网络。
- 非 root 运行，丢弃不必要的 Linux capabilities。
- 使用 namespaces、cgroups、seccomp 等隔离和资源控制。
- 限制 CPU、内存、进程数、文件大小、输出量和运行时间。
- 只读基础文件系统、每任务独立临时目录，结束后清理。
- 测试数据只读挂载并按任务授权访问。
- 不向 Runner 注入数据库密码、云密钥或长期凭证。
- 更新 Runner 镜像、宿主机并持续监控。
Docker 容器只是隔离的一层，不应单独视为充分安全边界。上线前需安全评审和对抗性测试；早期仅限可信内部试用。

## 6. 核心数据实体
User、Role、UserRole、Classroom、ClassroomMember、Invitation；
SyllabusVersion、SyllabusNode、KnowledgeNode、Lesson、LessonTemplate、Example；
Problem、ProblemRevision、ProblemTag、ProblemKnowledge、TestcaseSet；
Submission、JudgeJob、JudgeResult；
Assignment、AssignmentProblem、AssignmentSubmission；
LearningEvent、LearningProgress、MistakeCandidate、TeacherReview、AuditLog。
题目与知识点多对多关联；提交关联用户和题目版本；作业关联班级、教师和题目版本；错题候选关联提交证据并由教师独立复核。

## 7. API 约定
统一前缀 /api/v1。初步资源：/auth、/users、/classrooms、/curriculum/versions、/knowledge-nodes、/lessons、/problems、/submissions、/judge-jobs、/assignments、/learning-progress、/mistakes。
列表分页；写接口校验对象归属；错误响应不得泄露隐藏测试数据、内部路径或密钥。FastAPI 自动生成 API 文档，仅在内部环境开放。

## 8. 测试与交付
单元测试覆盖权限、状态机和评分逻辑；集成测试覆盖数据库、队列和提交到结果全链路；安全测试覆盖越权、隐藏数据泄露、资源耗尽和 Runner 隔离；前端测试覆盖登录、知识点浏览、提交和作业流程。CI 执行格式检查、静态检查、测试、构建和依赖漏洞检查。生产备份需定期演练恢复。

## 9. 部署建议
内部 MVP 可采用 Web/API 节点、PostgreSQL/Redis 数据服务和独立 Runner 主机。数据库与 Runner 尽可能分离；Runner 不与持有生产密钥的服务共享高权限环境。先实现开发、测试、生产配置隔离，再增加监控与备份。

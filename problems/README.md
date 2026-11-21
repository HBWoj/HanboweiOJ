# Problem packages

本目录存放原创题目包与样例测试配置。题目包按稳定 ID 和版本管理。

建议结构：

~~~text
problems/
  beginner/
    array-sum/
      problem.yaml
      statement.md
      samples/
      tests/
        manifest.json
        # 隐藏测试文件应使用受控存储，不随公开仓库发布
      solution/
        reference.cpp
        explanation.md
~~~

## 规则
- 公开仓库不得包含生产环境密钥或需要保密的评测基础设施信息。
- 用于教学的题目和题解优先原创。
- 隐藏测试数据与标准输出不得由公开题目接口读取。
- 如果题目源自第三方，必须记录许可和来源；未获授权的题目不导入。
- 题目发布前完成独立审题和数据验证。

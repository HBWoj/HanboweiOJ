# Curriculum content

本目录存放版本化的课程定义、知识点元数据、原创讲解与模板。

建议目录结构：

~~~text
curriculum/
  syllabus/
    noi-2025/
      manifest.yaml        # 来源、版本、页码映射和审核信息，不存放大纲全文
      mapping.yaml         # 站内知识点 ID 与大纲条目映射
  topics/
    beginner/
    intermediate/
    noi/
  templates/
    topic.schema.json
  lessons/
    beginner/
~~~

## 内容规则
- 课程条目使用稳定 ID，避免用标题作为外键。
- 明确前置知识与可观察的学习目标。
- 课程解释、示例代码和例题由本站原创编写。
- NOI 大纲作为覆盖映射来源，记录版本与页码/章节，不复制官方 PDF 的完整内容或页面。
- 每次课程结构变化都保留版本与审核记录。
- 未审核的条目保持 draft，不进入学生学习路径。

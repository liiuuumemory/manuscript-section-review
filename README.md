# manuscript-section-review

一个 Claude Skill，用于逐节审阅学术论文稿件。

- 每段给出英文原文、中文翻译，以及以引用分析为主的注释。
- 审阅期间不改稿件。所有意见和决定都记进一份审阅记录，包括编号、状态和中英文草稿。
- 用源数据和下载的参考文献原文核实每一处数值和引用。
- 审完后清点待定条目，并生成一份交接 prompt，交给新会话执行修改。

用法和规则见 [SKILL.md](SKILL.md)。

## 安装

**Claude Code**

```bash
git clone https://github.com/liiuuumemory/manuscript-section-review.git ~/.claude/skills/manuscript-section-review
```

重开会话后生效。说"逐节审阅我的稿件"之类的话就会触发，也可以输入 `/manuscript-section-review`。

**Claude 网页版 / 桌面 App**

把这个仓库下载为 zip，在 Settings → Capabilities → Skills 中上传。

## 依赖

"引用的原文核对"这一步用到 `scripts/extract_fulltext.py`，它需要 `pdftotext`（poppler）：

```bash
brew install poppler
```

其他步骤不需要额外依赖。

## 文件

```
SKILL.md                                技能说明和工作流程
references/review_log_template.md       审阅记录模板（示例条目为虚构）
references/handoff_prompt_template.md   交接 prompt 模板
scripts/extract_fulltext.py             把下载的 PDF/网页匹配到参考文献编号并提取全文
```

## 个性化

`SKILL.md` 中的"作者偏好"一节是原作者审稿时的习惯，例如补充材料"能删的统统删掉"、不用破折号。可以按自己的习惯修改。

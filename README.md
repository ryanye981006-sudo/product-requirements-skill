# 产品需求文档

调用 `$product-requirements`，提供需求描述、现有 PRD、原型代码或设计稿。按 [文风规则](文风.md) 组织增量需求，并执行 [输出校验](references/输出校验.md)。

## 安装与调用

将仓库克隆到 Codex 技能目录，目录名称使用 `product-requirements`。

```text
git clone https://github.com/ryanye981006-sudo/product-requirements-skill.git ~/.codex/skills/product-requirements
```

安装后在 Codex 中调用 `$product-requirements`，例如“根据这些材料整理本次需求，输出可导入语雀的 lake 文件”，或“把这份 PRD 转成可逐行复制到语雀的 HTML”。

## 交付方式

- 写 PRD、整理或优化需求，未指定格式时交付 Markdown。
- 要求导入语雀，生成 `.lake` 文件，通过语雀导入功能选择文件。
- 要求复制到语雀，生成独立 HTML，点击【复制本行】，在语雀目标行第一格粘贴。目标行原内容会被替换。
- 要求两种语雀格式，同时生成内容一致的 `.lake` 和 `_语雀复制.html`。
- 仅要求格式转换时保留原文，内容问题在交付说明中提示。

## 本地验证

Python 3，脚本使用标准库。

```text
python scripts/validate_lake.py "需求.lake"
python scripts/convert.py "需求.md" --output "需求_语雀复制.html"
python -m unittest discover -s scripts -p "test_*.py"
```

浏览器复制回归需要 Playwright，可通过 `PLAYWRIGHT_MODULE` 指向已安装模块，`BROWSER_CHANNEL=chrome` 使用本机 Chrome，`PYTHON` 指定 Python。

```text
node scripts/test_copy.cjs
```

lake 的结构检查、浏览器复制检查和语雀实际导入或粘贴分别报告。转换器支持范围和适配要求见 [SKILL.md](SKILL.md)，实际平台验证步骤见 [语雀实测](references/yuque-paste.md)。文风文件包含规则、场景示例及样本使用原则。

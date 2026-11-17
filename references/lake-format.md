# 语雀导入文件格式

用于交付 `.lake`。格式依据原有 `spec-new/lake-format.md` 及项目中的 lake 文件样本整理。平台接受情况通过实际导入验证。

## 文档头

保存为 UTF-8，使用以下骨架，标题替换为本次文档名称。

```html
<!doctype lake><title>需求文档</title><meta name="doc-version" content="1" /><meta name="viewport" content="adapt" /><meta name="typography" content="classic" /><meta name="paragraphSpacing" content="relax" />
<h1 data-lake-id="a1000001" id="a1000001"><span>3 需求描述</span></h1>
```

正文直接接在元信息后，省略 html/head/body 外壳。文件包含四个 meta。HTML 属性使用合法半角引号，正文中的提示文案按来源保留，可用中文引号引用。

## 章节与 ID

章节服从本次需求及已有结构。章用 h1，节用 h2，小节用 h3。文档名放在 title 中。

只有标题和 table 设置 `data-lake-id` 与 `id`，同一元素两者相等，各元素 ID 全文唯一，使用6至8位字母数字。其他节点无需 ID。

## 表格

```html
<table data-lake-id="t1000001" id="t1000001" margin="true" class="lake-table" style="width: 840px"><colgroup><col width="166"><col width="424"><col width="250"></colgroup><tbody><tr><td><p><span>功能项</span></p></td><td><p><span>描述</span></p></td><td><p><span>图例</span></p></td></tr><tr><td><p><span>查询</span></p></td><td><ol list="L01"><li><span>按输入条件返回结果。</span></li></ol></td><td><p><span></span></p></td></tr></tbody></table>
```

三列需求表采用166、424、250，总宽840。其他表格按源列数生成 col 和 td，并分配相应宽度，列宽之和与表格宽度一致。表头与数据行列数一致，空图例保留 td。功能项默认普通文本，来源已加粗时保留。

## 编号与层级

```html
<ol list="L01"><li><span>第一条。</span></li><li><span>第二条，包含以下条件。</span></li></ol><ol list="L01" data-lake-indent="1"><li><span>第一个子条件。</span></li><li><span>第二个子条件。</span></li></ol><ol list="L01" start="3"><li><span>第三条。</span></li></ol>
```

- 同一单元格的顶层编号共享 list 值，不同单元格使用不同 list 值。
- 子条件用相邻 ol 的 `data-lake-indent="1"` 表示，更深层递增。返回上层时用 `start` 接续该层编号。
- 子列表归属前一个父条目，新父条目的子列表可从1开始。
- 相邻 ol 块直接拼接，避免中间空白被显示为空行。
- li 内文本不再手写数字序号。换行用于普通文本，规则序列使用 ol/li。

## 文本与其他内容

- 普通段落用 `<p><span>文本</span></p>`，文本中的 `&`、`<`、`>` 正确转义。
- 加粗用 `<span style="font-weight: bold">重点</span>`。链接用合法 a 标签，保留原链接目标。
- 图片采用原有格式约定 `<card type="inline" name="image" value="URL-encoded JSON" />`。具体图片 JSON 结构从可用导出样本核实，未知属性须先验证，已有图片和图例不能静默丢失。新文档没有图例时留空格。
- 暂缓、删除线和待定状态须保留语义。遇到未验证的富文本形式时，明确限制并核验具体节点，避免把旧规则导入为有效需求。

## 校验

运行 `scripts/validate_lake.py`，检查文档头、四项元信息、标签闭合、ID、表格列数与列表属性。然后根据最终底稿核对逐格文字、顺序、数字、条件、加粗、列表层级、链接和图例。结构检查不能验证业务内容或平台导入结果。

两种格式同时交付时，分别从同一最终底稿生成。HTML 页面上的复制控件和脚本只属于复制版，lake 仅包含需求内容。

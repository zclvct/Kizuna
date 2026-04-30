# Markdown 渲染器 — 将 Markdown 转换为带样式的 HTML
import markdown as md_lib


def render_markdown(text: str) -> str:
    """将 Markdown 文本转换为带内联样式的 HTML

    支持：代码高亮、表格、有序/无序列表、任务列表、链接等
    """
    try:
        html = md_lib.markdown(
            text,
            extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "toc",
                "nl2br",
                "sane_lists",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": False,
                    "noclasses": True,
                },
            },
        )
    except Exception:
        html = text.replace("\n", "<br>")

    return html


# ── 内联 CSS（注入到每个 QTextBrowser）──────────────────────────────

MESSAGE_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #333;
    background: transparent;
    margin: 0;
    padding: 0;
}
p { margin: 0.3em 0; }
ul, ol { margin: 0.3em 0; padding-left: 1.5em; }
li { margin: 0.15em 0; }
pre {
    background: #1e1e2e;
    color: #cdd6f4;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 0.4em 0;
    overflow-x: auto;
    font-size: 12px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
}
code {
    background: rgba(135, 150, 180, 0.15);
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 12px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
}
pre code {
    background: transparent;
    padding: 0;
}
table {
    border-collapse: collapse;
    margin: 0.5em 0;
    font-size: 12px;
    width: 100%;
}
th, td {
    border: 1px solid #ddd;
    padding: 4px 8px;
    text-align: left;
}
th {
    background: #f5f5f5;
    font-weight: 600;
}
blockquote {
    border-left: 3px solid #7BB8FF;
    margin: 0.4em 0;
    padding: 0.2em 0.8em;
    color: #666;
    background: rgba(123, 184, 255, 0.06);
    border-radius: 0 4px 4px 0;
}
h1, h2, h3, h4 { margin: 0.5em 0 0.2em; }
h1 { font-size: 18px; }
h2 { font-size: 16px; }
h3 { font-size: 14px; }
a { color: #5c9eff; text-decoration: none; }
a:hover { text-decoration: underline; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 0.6em 0; }
/* 任务列表 */
.task-list-item { list-style: none; margin-left: -1.5em; }
.task-list-item input { margin-right: 0.5em; }
"""

# 用户消息专用 CSS（白色文字，适配蓝色气泡背景）
USER_MESSAGE_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #fff;
    background: transparent;
    margin: 0;
    padding: 0;
}
p { margin: 0.3em 0; }
ul, ol { margin: 0.3em 0; padding-left: 1.5em; }
li { margin: 0.15em 0; }
pre {
    background: rgba(0, 0, 0, 0.15);
    color: #f0f0f0;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 0.4em 0;
    overflow-x: auto;
    font-size: 12px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
}
code {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 12px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
}
pre code {
    background: transparent;
    padding: 0;
}
table {
    border-collapse: collapse;
    margin: 0.5em 0;
    font-size: 12px;
    width: 100%;
}
th, td {
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 4px 8px;
    text-align: left;
}
th {
    background: rgba(255, 255, 255, 0.1);
    font-weight: 600;
}
blockquote {
    border-left: 3px solid rgba(255, 255, 255, 0.5);
    margin: 0.4em 0;
    padding: 0.2em 0.8em;
    color: rgba(255, 255, 255, 0.8);
    border-radius: 0 4px 4px 0;
}
h1, h2, h3, h4 { margin: 0.5em 0 0.2em; }
h1 { font-size: 18px; }
h2 { font-size: 16px; }
h3 { font-size: 14px; }
a { color: #fff; text-decoration: underline; }
hr { border: none; border-top: 1px solid rgba(255, 255, 255, 0.3); margin: 0.6em 0; }
.task-list-item { list-style: none; margin-left: -1.5em; }
.task-list-item input { margin-right: 0.5em; }
"""

DEBUG_CSS = """
body {
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 11px;
    line-height: 1.5;
    color: #555;
    background: transparent;
    margin: 0;
    padding: 0;
}
p { margin: 0.2em 0; }
pre {
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 4px;
    padding: 6px 8px;
    margin: 0.3em 0;
    overflow-x: auto;
    font-size: 11px;
}
code {
    font-size: 11px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
}
a { color: #5c9eff; text-decoration: none; }
"""

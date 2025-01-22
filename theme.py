from toolbox import get_conf

CODE_HIGHLIGHT = True

def adjust_theme():
    return None

advanced_css = """
/* Set regular font */
.markdown-body {
    font-family: "Helvetica Neue", Helvetica, "Segoe UI", Arial, freesans, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    font-size: 16px;
    line-height: 1.6;
    word-wrap: break-word;
}

/* Set code block font */
.markdown-body code, .markdown-body pre {
    font-family: Monaco, Menlo, Consolas, "Courier New", monospace;
    font-size: 12px;
}

/* Set code block style */
.markdown-body pre {
    margin-top: 0;
    margin-bottom: 0;
    font: 12px Monaco, Menlo, Consolas, "Courier New", monospace;
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: #f7f7f7;
    border-radius: 3px;
}

/* Set inline code style */
.markdown-body code {
    padding: 0;
    padding-top: 0.2em;
    padding-bottom: 0.2em;
    margin: 0;
    font-size: 85%;
    background-color: rgba(0,0,0,0.04);
    border-radius: 3px;
}

/* Set inline code padding */
.markdown-body code:before,
.markdown-body code:after {
    letter-spacing: -0.2em;
    content: "\\00a0";
}

/* Set pre code style */
.markdown-body pre > code {
    padding: 0;
    margin: 0;
    font-size: 100%;
    word-break: normal;
    white-space: pre;
    background: transparent;
    border: 0;
}

/* Set pre code padding */
.markdown-body pre code:before,
.markdown-body pre code:after {
    content: normal;
}

/* Set blockquote style */
.markdown-body blockquote {
    padding: 0 15px;
    color: #777;
    border-left: 4px solid #ddd;
    margin: 0;
    margin-bottom: 16px;
}

/* Set blockquote margin */
.markdown-body blockquote > :first-child {
    margin-top: 0;
}

/* Set blockquote margin */
.markdown-body blockquote > :last-child {
    margin-bottom: 0;
}

/* Set table style */
.markdown-body table {
    display: block;
    width: 100%;
    overflow: auto;
    margin: 16px 0;
    border-spacing: 0;
    border-collapse: collapse;
}

/* Set table cell style */
.markdown-body table th,
.markdown-body table td {
    padding: 6px 13px;
    border: 1px solid #ddd;
}

/* Set table header style */
.markdown-body table th {
    font-weight: bold;
}

/* Set table row style */
.markdown-body table tr {
    background-color: #fff;
    border-top: 1px solid #ccc;
}

/* Set table alternate row style */
.markdown-body table tr:nth-child(2n) {
    background-color: #f8f8f8;
}

/* Set image style */
.markdown-body img {
    max-width: 100%;
    box-sizing: content-box;
    background-color: #fff;
}

/* Set horizontal rule style */
.markdown-body hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e1e4e8;
    border: 0;
}
"""

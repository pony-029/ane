#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync v0.8.0 chapters (38-42) and Appendix I from the Chinese DEBUG markdown
into the Chinese DEBUG HTML. Deterministic and repeatable."""
import html
import pathlib
import re

BASE = pathlib.Path(__file__).resolve().parent.parent
MD = BASE / "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.md"
HTML = BASE / "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.html"


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def convert(md_text, id_start=38, id_override=None):
    lines = md_text.split("\n")
    out, paragraph = [], []
    section_open = False
    counter = id_start

    def flush():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            flush()
            i += 1
            continue
        if line.startswith("## "):
            flush()
            if section_open:
                out.append("</section>")
            title = line[3:].strip()
            if id_override:
                sid = id_override
            else:
                sid = "ch%d" % counter
                counter += 1
            parts = title.split("　", 1)
            num = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            out.append('<section id="%s">' % sid)
            out.append('<h2 class="sec"><span class="num">%s</span>%s</h2>' % (inline(num), inline(rest)))
            section_open = True
            i += 1
            continue
        if line.startswith("### "):
            flush()
            out.append("<h3>" + inline(line[4:].strip()) + "</h3>")
            i += 1
            continue
        if line.startswith("> "):
            flush()
            out.append('<div class="callout quote">' + inline(line[2:].strip()) + "</div>")
            i += 1
            continue
        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append(
                '<pre style="background:var(--surface);border:1px solid var(--line);border-radius:12px;'
                'padding:18px;overflow-x:auto;font-size:12.5px;color:var(--ink2)"><code>'
                + html.escape("\n".join(buf), quote=False) + "</code></pre>"
            )
            i = j + 1
            continue
        if line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            parsed = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            header = parsed[0]
            body = parsed[2:]
            out.append('<div class="tw"><table><thead><tr>')
            out.extend("<th>" + inline(c) + "</th>" for c in header)
            out.append("</tr></thead><tbody>")
            for row in body:
                out.append("<tr>")
                out.extend("<td>" + inline(c) + "</td>" for c in row)
                out.append("</tr>")
            out.append("</tbody></table></div>")
            continue
        if re.match(r"^-\s", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^-\s", lines[i]):
                items.append(re.sub(r"^-\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>" + inline(x) + "</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>" + inline(x) + "</li>" for x in items) + "</ol>")
            continue
        if line == "---":
            flush()
            i += 1
            continue
        paragraph.append(line.strip())
        i += 1
    flush()
    if section_open:
        out.append("</section>")
    return "\n".join(out)


def main():
    md = MD.read_text(encoding="utf-8")
    h = HTML.read_text(encoding="utf-8")

    ch_md = md[md.index("## 第三十八章"):md.index("## 附录 A")]
    ap_md = md[md.index("## 附录 I"):md.index("> **结语**")]
    ch_html = convert(ch_md, id_start=38)
    ap_html = convert(ap_md, id_override="appi")

    anchor = "<!-- ================= APPENDIX A ================= -->"
    if anchor not in h:
        raise SystemExit("APPENDIX A anchor not found")
    h = h.replace(anchor, ch_html + "\n\n" + anchor, 1)

    if '<footer>' not in h:
        raise SystemExit("footer anchor not found")
    h = h.replace("<footer>", ap_html + "\n\n<footer>", 1)

    HTML.write_text(h, encoding="utf-8")
    print("synced chapters 38-42 and appendix I into DEBUG HTML")
    print("sections:", h.count("<section"), "tables:", h.count("<table"))


if __name__ == "__main__":
    main()

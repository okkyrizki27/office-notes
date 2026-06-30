"""
Generate PDF for Digiman Transaction Report — Gap Analysis & Discussion Document.
Run: python generate_pdf.py
Input : gap-analysis.md
Output: Digiman_Transaction_Report_Gap_Analysis.pdf (same folder)
"""

import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(BASE_DIR, "gap-analysis.md")
HTML_FILE = os.path.join(BASE_DIR, "Digiman_Transaction_Report_Gap_Analysis.html")
PDF_FILE = os.path.join(BASE_DIR, "Digiman_Transaction_Report_Gap_Analysis.pdf")


def md_to_html(md):
    html_lines = []
    in_table = False
    for line in md.split("\n"):
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
            continue

        if line.strip() == "---":
            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False
            html_lines.append("<hr>")
            continue

        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.replace("-", "").replace(":", "")) == set() for c in cells):
                continue
            if not in_table:
                html_lines.append("<table><thead>")
                in_table = True
                tag = "th"
            else:
                tag = "td"

            def fmt_cell(c):
                c = re.sub(r"`([^`]+)`", r"<code>\1</code>", c)
                c = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", c)
                c = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", c)
                c = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', c)
                return c

            html_lines.append(
                "<tr>" + "".join(f"<{tag}>{fmt_cell(c)}</{tag}>" for c in cells) + "</tr>"
            )
            if tag == "th":
                html_lines.append("</thead><tbody>")
            continue
        else:
            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False

        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", line)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line)

        if line.strip() == "":
            html_lines.append("<br>")
        elif line.strip().startswith("<div") or line.strip().startswith(">"):
            if line.strip().startswith(">"):
                html_lines.append(f"<blockquote>{line.strip()[1:].strip()}</blockquote>")
            else:
                html_lines.append(line)
        else:
            html_lines.append(f"<p>{line}</p>")

    if in_table:
        html_lines.append("</tbody></table>")
    return "\n".join(html_lines)


with open(MD_FILE, encoding="utf-8") as f:
    md_content = f.read()

html_body = md_to_html(md_content)

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Digiman Transaction Report - Gap Analysis</title>
<style>
  @page {{ size: A4 portrait; margin: 16mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1a1a1a; padding: 0 60px; margin: 0; }}
  h1 {{ font-size: 19pt; color: #1f3a5f; border-bottom: 3px solid #1f3a5f; padding-bottom: 8px; margin-bottom: 6px; }}
  h2 {{ font-size: 13.5pt; color: #fff; background: #1f3a5f; padding: 7px 12px; border-radius: 3px; margin: 24px 0 10px; page-break-after: avoid; break-after: avoid; }}
  h3 {{ font-size: 11.5pt; color: #1f3a5f; border-left: 4px solid #1f3a5f; padding-left: 10px; margin: 18px 0 8px; page-break-after: avoid; break-after: avoid; }}
  table {{ width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 8.3pt; margin: 8px 0 14px; }}
  th {{ background: #1f3a5f; color: #fff; padding: 6px 7px; text-align: left; font-weight: 600; word-wrap: break-word; }}
  td {{ padding: 5px 7px; border-bottom: 1px solid #e0e0e0; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; }}
  tr {{ page-break-inside: avoid; break-inside: avoid; }}
  tr:nth-child(even) td {{ background: #f4f7fa; }}
  code {{ background: #f0f0f0; color: #1a1a1a; padding: 1px 5px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9pt; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 16px 0; }}
  a {{ color: #1f3a5f; text-decoration: none; }}
  p {{ margin: 4px 0; line-height: 1.6; }}
  b {{ color: #111; }}
  blockquote {{ margin: 8px 0; padding: 8px 14px; background: #f4f7fa; border-left: 4px solid #1f3a5f; font-style: italic; color: #333; }}
  .sev-high {{ display:inline-block; color:#fff; background:#c0392b; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .sev-medium {{ display:inline-block; color:#fff; background:#d68910; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .sev-low {{ display:inline-block; color:#fff; background:#7f8c8d; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .sev-pending {{ display:inline-block; color:#fff; background:#2c3e50; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .sev-resolved {{ display:inline-block; color:#fff; background:#1e8449; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .sev-open {{ display:inline-block; color:#fff; background:#7d3c98; padding:1px 7px; border-radius:3px; font-size:8pt; font-weight:bold; }}
  .footer {{ margin-top: 30px; font-size: 9pt; color: #888; text-align: center; border-top: 1px solid #ddd; padding-top: 8px; }}
  @media print {{ h2, th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} body {{ padding: 0 30px; }} }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"HTML saved: {HTML_FILE}")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
file_url = "file:///" + HTML_FILE.replace("\\", "/").replace(" ", "%20")
result = subprocess.run(
    [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_FILE}",
        file_url,
    ],
    capture_output=True,
)
if os.path.exists(PDF_FILE):
    print(f"PDF saved: {PDF_FILE}")
else:
    print("PDF generation failed.")
    print(result.stderr.decode(errors="ignore"))

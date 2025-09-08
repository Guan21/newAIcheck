import json
from jinja2 import Template
from datetime import datetime

def main():
    with open("output/repos.json", "r", encoding="utf-8") as f:
        repos = json.load(f)
    with open("report_template.md", "r", encoding="utf-8") as f:
        template_str = f.read()
    template = Template(template_str)
    md = template.render(repos=repos)
    # ファイル名: {プロジェクト名}_{作成日}.md
    if repos:
        proj_name = repos[0]["name"]
    else:
        proj_name = "report"
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"output/{proj_name}_{date_str}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"{filename} を生成しました。")

if __name__ == "__main__":
    main()

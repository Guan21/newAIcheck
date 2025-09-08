import os
import json
import re
import openai
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def ai_summarize(text):
    prompt = (
        "以下のREADME.md内容から、このプロジェクトの『用途』『使い方』に関するポイントを日本語で3点要約してください。\n"
        "コマンド例や利用シーン、導入方法なども含めて簡潔にまとめてください。\n"
        "### 内容:\n" + text
    )
    last_error = None
    for attempt in range(3):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは優秀なAIプロジェクト分析者です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=256,
                temperature=0.4
            )
            summary = response["choices"][0]["message"]["content"]
            lines = [line.strip("-・ ") for line in summary.splitlines() if line.strip()]
            return [line for line in lines if line]
        except Exception as e:
            last_error = str(e)
            print(f"OpenAI要約失敗（{attempt+1}回目）: {e}")
    return [f"AI要約失敗: {last_error}"]

def extract_usage_from_readme(readme_path):
    usage = []
    if not os.path.isfile(readme_path):
        return usage
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Usageセクション抽出
        usage_match = re.search(r"(?:^|\n)#+\s*Usage[^\n]*\n(.*?)(?:\n#+|\Z)", content, re.IGNORECASE | re.DOTALL)
        if usage_match:
            usage_text = usage_match.group(1).strip()
            usage.append(usage_text)
        # コードブロック抽出
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9]*)\n(.*?)```", content, re.DOTALL)
        usage.extend([cb.strip() for cb in code_blocks])
    return usage

REPOS_JSON = "output/repos.json"
REPOS_DIR = "repos"

TECH_KEYWORDS = [
    ("Playwright", "Playwright MCP"),
    ("Claude", "Claude Code"),
    ("Anthropic", "Anthropic Claude"),
    ("Python", "Python"),
    ("Node.js", "Node.js"),
    ("TensorFlow", "TensorFlow"),
    ("PyTorch", "PyTorch"),
    ("OpenAI", "OpenAI"),
    ("HuggingFace", "HuggingFace"),
    ("Google AI", "Google AI"),
    ("Azure AI", "Azure AI")
]

def extract_info_from_readme(readme_path):
    tech = set()
    features = set()
    ai_providers = set()
    ai_features = []
    contents = []
    # README.md
    if os.path.isfile(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            contents.append(f.read())
    else:
        # GitHub rawからREADME.md取得
        repo_name = os.path.basename(os.path.dirname(readme_path))
        full_name = None
        # repos.jsonからfull_name取得
        try:
            with open("output/repos.json", "r", encoding="utf-8") as rf:
                all_repos = json.load(rf)
                for r in all_repos:
                    if r.get("name") == repo_name:
                        full_name = r.get("full_name")
                        break
        except Exception:
            pass
        if full_name:
            import requests
            raw_url = f"https://raw.githubusercontent.com/{full_name}/main/README.md"
            try:
                resp = requests.get(raw_url, timeout=10)
                if resp.status_code == 200:
                    contents.append(resp.text)
            except Exception:
                pass
    # requirements.txt
    req_path = os.path.join(os.path.dirname(readme_path), "requirements.txt")
    if os.path.isfile(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            contents.append(f.read())
    # package.json
    pkg_path = os.path.join(os.path.dirname(readme_path), "package.json")
    if os.path.isfile(pkg_path):
        try:
            pkg = json.load(open(pkg_path, "r", encoding="utf-8"))
            deps = pkg.get("dependencies", {})
            tech.update(deps.keys())
        except Exception:
            pass
    # main.py, app.js
    for fname in ["main.py", "app.js"]:
        fpath = os.path.join(os.path.dirname(readme_path), fname)
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                contents.append(f.read())
    # 解析
    for content in contents:
        for kw, label in TECH_KEYWORDS:
            if re.search(kw, content, re.IGNORECASE):
                if "AI" in label or "Claude" in label or "OpenAI" in label or "HuggingFace" in label:
                    ai_providers.add(label)
                elif "Playwright" in label or "Python" in label or "Node.js" in label or "TensorFlow" in label or "PyTorch" in label:
                    tech.add(label)
        feature_patterns = [
            r"デザインレビュー", r"自動化", r"チェック", r"認識", r"分類", r"アクセシビリティ", r"UI/UX", r"自然言語処理", r"チャットボット", r"画像認識"
        ]
        for pat in feature_patterns:
            if re.search(pat, content):
                features.add(pat)
        if "README" in readme_path:
            ai_features = ai_summarize(content)
    return list(tech), list(features), list(ai_providers), ai_features

def main():
    os.makedirs("output", exist_ok=True)
    if not os.path.isfile(REPOS_JSON):
        print("repos.jsonがありません。新規作成します。")
        repos = []
    else:
        with open(REPOS_JSON, "r", encoding="utf-8") as f:
            repos = json.load(f)
    for repo in repos:
        repo_dir = repo.get("path", os.path.join("AICheck", repo["name"]))
        readme_path = os.path.join(repo_dir, "README.md")
        tech, features, ai_providers, ai_features = extract_info_from_readme(readme_path)
        usage = extract_usage_from_readme(readme_path)
        # 必ず項目を上書き
        repo["技術スタック"] = tech if tech else ["情報抽出できませんでした"]
        repo["主な用途・使い方"] = ai_features if ai_features else features if features else ["情報抽出できませんでした"]
        repo["Usage例"] = usage if usage else ["情報抽出できませんでした"]
        repo["利用AI Provider"] = ai_providers if ai_providers else ["情報抽出できませんでした"]
    with open(REPOS_JSON, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print("READMEのusage情報をrepos.jsonへ保存しました。")

if __name__ == "__main__":
    main()

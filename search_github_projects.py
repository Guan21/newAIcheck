import requests
import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com/search/repositories"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def generate_search_query(user_input):
    prompt = (
        "You are a GitHub project search agent. "
        "Given the following purpose/requirement (in Japanese), output a single line GitHub search query using English keywords and official GitHub search syntax (e.g. automation language:Python). "
        "Do NOT include any Japanese or explanations, only the query.\n"
        f"Purpose/Requirement: {user_input}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled GitHub search agent."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=64,
        temperature=0.3
    )
    query = response["choices"][0]["message"]["content"].strip()
    return query

def search_github_repos(query):
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 20
    }
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(GITHUB_API_URL, params=params, headers=headers)
    response.raise_for_status()
    repos = response.json().get("items", [])
    return repos

def summarize_repos(repos, user_input):
    repo_summaries = []
    for repo in repos:
        summary = {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "clone_url": repo["clone_url"],
            "stars": repo["stargazers_count"],
            "html_url": repo["html_url"],
            "description": repo.get("description", ""),
            "path": os.path.join("repos", repo["name"])
        }
        repo_summaries.append(summary)
    # AIによる推奨・要約
    prompt = (
        f"以下はGitHub検索結果です。目的: {user_input}\n"
        "各プロジェクトの特徴・推奨理由を日本語で簡潔にまとめ、目的に合致する順に並べてJSON形式で出力してください。\n"
        "### 検索結果:\n" + json.dumps(repo_summaries, ensure_ascii=False, indent=2)
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはGitHubプロジェクト選定AIです。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024,
        temperature=0.4
    )
    ai_result = response["choices"][0]["message"]["content"]
    try:
        recommended = json.loads(ai_result)
    except Exception:
        recommended = repo_summaries
    return recommended

def main():
    user_input = input("GitHub検索の目的・条件を日本語で入力してください: ")
    print("AIAgentが検索クエリを生成中...")
    query = generate_search_query(user_input)
    print(f"生成クエリ: {query}")
    print("GitHub APIで検索中...")
    repos = search_github_repos(query)
    print(f"検出リポジトリ数: {len(repos)}")
    print("AIAgentが検索結果を要約・レコメンド中...")
    recommended = summarize_repos(repos, user_input)
    os.makedirs("output", exist_ok=True)
    with open("output/repos.json", "w", encoding="utf-8") as f:
        json.dump(recommended, f, ensure_ascii=False, indent=2)
    print("推奨プロジェクト一覧をoutput/repos.jsonに保存しました。")

if __name__ == "__main__":
    main()

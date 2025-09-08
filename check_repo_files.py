import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
REPOS_DIR = os.environ.get("CLONE_DIR", "repos")
RESULT_FILE = "output/check_results.json"

LOG_FILE = "logs/all.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [check_repo_files.py] %(message)s",
    encoding="utf-8"
)

def check_files(repo_path):
    readme_exists = os.path.isfile(os.path.join(repo_path, "README.md"))
    dockerfile_exists = os.path.isfile(os.path.join(repo_path, "Dockerfile"))
    return readme_exists, dockerfile_exists

def main():
    results = []
    if not os.path.exists(REPOS_DIR):
        msg = "repos ディレクトリがありません。先にclone処理を実行してください。"
        print(msg)
        logging.info(msg)
        return

    for repo_name in os.listdir(REPOS_DIR):
        repo_path = os.path.join(REPOS_DIR, repo_name)
        if os.path.isdir(repo_path):
            readme, dockerfile = check_files(repo_path)
            results.append({
                "repo_name": repo_name,
                "path": repo_path,
                "readme": readme,
                "dockerfile": dockerfile
            })

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    msg = f"チェック結果を {RESULT_FILE} に保存しました。"
    print(msg)
    logging.info(msg)

if __name__ == "__main__":
    main()

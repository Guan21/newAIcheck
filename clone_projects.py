import os
import subprocess
import json
import argparse
import logging
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = "logs/all.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [clone_projects.py] %(message)s",
    encoding="utf-8"
)

def clone_repo(clone_url, repo_name, base_dir):
    target_dir = os.path.join(base_dir, repo_name)
    need_clone = False
    if not os.path.exists(target_dir):
        need_clone = True
    elif not os.listdir(target_dir):
        msg = f"{repo_name} exists but is empty. Re-cloning ..."
        print(msg)
        logging.info(msg)
        need_clone = True
    if need_clone:
        msg = f"Cloning {repo_name} ..."
        print(msg)
        logging.info(msg)
        try:
            subprocess.run(["git", "clone", clone_url, target_dir], check=True)
        except subprocess.CalledProcessError as e:
            msg = f"Clone failed for {repo_name}: {e}"
            print(msg)
            logging.info(msg)
        except Exception as e:
            msg = f"Unexpected error for {repo_name}: {e}"
            print(msg)
            logging.info(msg)
    else:
        msg = f"{repo_name} already exists. Skipping."
        print(msg)
        logging.info(msg)

def main():
    parser = argparse.ArgumentParser(description="GitHubリポジトリを指定ディレクトリにclone")
    parser.add_argument("--dir", default=None, help="clone先ディレクトリ (環境変数CLONE_DIR優先、未指定時はrepos)")
    args = parser.parse_args()

    env_dir = os.environ.get("CLONE_DIR")
    base_dir = args.dir if args.dir else (env_dir if env_dir else "repos")

    repos_json = "repos.json"
    if not os.path.exists(repos_json):
        msg = "repos.json が見つかりません。先に検索スクリプトを実行してください。"
        print(msg)
        logging.info(msg)
        return

    with open(repos_json, "r", encoding="utf-8") as f:
        repos = json.load(f)

    os.makedirs(base_dir, exist_ok=True)
    for repo in repos:
        clone_repo(repo["clone_url"], repo["name"], base_dir)
        repo["path"] = os.path.join(base_dir, repo["name"])
    # クローン後にpathキーをrepos.jsonへ保存
    with open(repos_json, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

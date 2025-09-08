import os
import json
import subprocess
import openai
import logging
from dotenv import load_dotenv

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
RESULT_FILE = os.path.join(OUTPUT_DIR, "check_results.json")
TEST_RESULT_FILE = os.path.join(OUTPUT_DIR, "test_results.json")
AI_REPORT_FILE = os.path.join(OUTPUT_DIR, "ai_summary_report.md")

LOG_FILE = "logs/all.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [docker_test_runner.py] %(message)s",
    encoding="utf-8"
)

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def run_docker_build_and_test(repo_path, repo_name):
    build_cmd = ["docker", "build", "-t", f"{repo_name.lower()}_img", repo_path]
    print(f"[{repo_name}] Dockerビルド開始...")
    try:
        build_result = subprocess.run(build_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        build_success = build_result.returncode == 0
        build_log = build_result.stdout + "\n" + build_result.stderr
    except subprocess.TimeoutExpired:
        build_success = False
        build_log = "Dockerビルドがタイムアウトしました。"
    except Exception as e:
        build_success = False
        build_log = str(e)

    test_success = None
    test_log = ""
    if build_success:
        print(f"[{repo_name}] Dockerテスト開始...")
        # テストコマンドはDockerfileのCMD/ENTRYPOINTに依存
        run_cmd = ["docker", "run", "--rm", f"{repo_name.lower()}_img"]
        try:
            test_result = subprocess.run(run_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=100)
            test_log = test_result.stdout + "\n" + test_result.stderr
            # 失敗やハングを検知して test_success を判定
            if test_result.returncode == 0 and not any(
                kw in test_log.lower() for kw in ["failed", "timeout", "error", "ハング", "停止"]
            ):
                test_success = True
            else:
                test_success = False
                logging.info(f"[{repo_name}] Dockerテスト失敗またはハング検知: {test_log[:200]}")
        except subprocess.TimeoutExpired:
            test_success = False
            test_log = "Dockerテストがタイムアウトしました。"
        except Exception as e:
            test_success = False
            test_log = str(e)
    else:
        print(f"[{repo_name}] Dockerビルド失敗: {build_log}")

    return {
        "repo_name": repo_name,
        "build_success": build_success,
        "build_log": build_log,
        "test_success": test_success,
        "test_log": test_log
    }

def main():
    if not os.path.exists(RESULT_FILE):
        msg = "check_results.json がありません。先にファイルチェックを実行してください。"
        print(msg)
        logging.info(msg)
        return

    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        repos = json.load(f)

    results = []
    for repo in repos:
        if repo["readme"] and repo["dockerfile"]:
            msg = f"Testing {repo['repo_name']} ..."
            print(msg)
            logging.info(msg)
            result = run_docker_build_and_test(repo["path"], repo["repo_name"])
            results.append(result)
        elif repo["readme"]:
            # Dockerfileがない場合は静的解析・AI要約
            readme_path = os.path.join(repo["path"], "README.md")
            static_result = {
                "repo_name": repo["repo_name"],
                "build_success": None,
                "build_log": "Dockerfileなし。静的解析のみ実施。",
                "test_success": None,
                "test_log": ""
            }
            try:
                with open(readme_path, "r", encoding="utf-8") as rf:
                    readme_content = rf.read()
                static_result["test_log"] = f"README内容抜粋:\n{readme_content[:1000]}"
            except Exception as e:
                static_result["test_log"] = f"README取得失敗: {e}"
            results.append(static_result)

    with open(TEST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    msg = f"テスト結果を {TEST_RESULT_FILE} に保存しました。"
    print(msg)
    logging.info(msg)

def summarize_test_results(test_results_path, output_report_path):
    if not os.path.isfile(test_results_path):
        msg = "test_results.jsonがありません"
        print(msg)
        logging.info(msg)
        return
    with open(test_results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    # ログ長制限：各ログ先頭1000文字＋末尾1000文字のみ抽出
    def trim_log(log, head=1000, tail=1000):
        if not log:
            return ""
        log = str(log)
        if len(log) <= head + tail:
            return log
        return log[:head] + "\n...省略...\n" + log[-tail:]
    summary_lines = []
    for r in results:
        summary_lines.append(f"リポジトリ: {r.get('repo_name','')}")
        summary_lines.append(f"build_success: {r.get('build_success','')}")
        summary_lines.append("build_log抜粋:\n" + trim_log(r.get('build_log','')))
        summary_lines.append(f"test_success: {r.get('test_success','')}")
        summary_lines.append("test_log抜粋:\n" + trim_log(r.get('test_log','')))
        summary_lines.append("-" * 40)
    summary_prompt = (
        "以下はAIプロジェクトのDockerテスト結果（長大なログは抜粋）です。主な特徴・エラー傾向・改善案を日本語で3点要約してください。\n"
        "### テスト結果:\n" + "\n".join(summary_lines)
    )
    last_error = None
    for attempt in range(3):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは優秀なAIプロジェクト検証エージェントです。"},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=512,
                temperature=0.4
            )
            summary = response["choices"][0]["message"]["content"]
            with open(output_report_path, "w", encoding="utf-8") as rf:
                rf.write("# AIテスト結果要約レポート\n\n")
                rf.write(f"対象: {test_results_path}\n")
                rf.write(f"要約日時: {__import__('datetime').datetime.now()}\n\n")
                rf.write("## 要約内容\n")
                rf.write(summary.strip() + "\n")
            msg = f"AI要約レポートを {output_report_path} に保存しました。"
            print(msg)
            logging.info(msg)
            return
        except Exception as e:
            last_error = str(e)
            msg = f"OpenAI要約失敗（{attempt+1}回目）: {e}"
            print(msg)
            logging.info(msg)
    with open(output_report_path, "w", encoding="utf-8") as rf:
        rf.write("# AIテスト結果要約レポート\n\n")
        rf.write(f"対象: {test_results_path}\n")
        rf.write(f"要約日時: {__import__('datetime').datetime.now()}\n\n")
        rf.write("## 要約失敗\n")
        rf.write(f"AI要約失敗: {last_error}\n")

if __name__ == "__main__":
    main()
    summarize_test_results(TEST_RESULT_FILE, AI_REPORT_FILE)

#!/bin/bash

# 対話型GitHub検索（AIAgent機能付き）
python3 search_github_projects.py

# クローン
python3 clone_projects.py

# ファイルチェック
python3 check_repo_files.py

# Readme解析＆repos.json更新
python3 generate_report.py

# Dockerテスト＆AI要約
python3 docker_test_runner.py

# Markdownレポート生成
python3 generate_markdown_report.py

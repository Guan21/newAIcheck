# AIプロジェクト分析レポート

{% for repo in repos %}
## {{ repo.name }}

- フルネーム: {{ repo.full_name }}
- スター数: {{ repo.stars }}
- リンク: [{{ repo.html_url }}]({{ repo.html_url }})

### 技術スタック
{{ repo["技術スタック"] | join(", ") }}

### 主な用途・使い方
{{ repo["主な用途・使い方"] | join("\n- ") }}

### Usage例
{{ repo["Usage例"] | join("\n```") }}

### 利用AI Provider
{{ repo["利用AI Provider"] | join(", ") }}

---

{% endfor %}

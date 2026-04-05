# tools.py — 既存ツール定義（パーミッション付き）
import subprocess
import urllib.request
import json
import csv
import os

def read_file(path: str) -> str:
    """ファイルを読み込んで内容を返す"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    """ファイルに書き込む"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"ファイルを書き込みました: {path}"

def list_directory(path: str = ".") -> str:
    """ディレクトリの内容を一覧する"""
    entries = os.listdir(path)
    return "\n".join(entries)

def run_shell(command: str) -> str:
    """シェルコマンドを実行する（サンドボックス内）"""
    result = subprocess.run(
        command, shell=True, capture_output=True,
        text=True, timeout=30
    )
    return result.stdout + result.stderr

def fetch_url(url: str) -> str:
    """URLからコンテンツを取得する"""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8')[:5000]

# ツールレジストリ（パーミッションレベル付き）
TOOL_REGISTRY = {
    "read_file": {"fn": read_file, "permission": "read"},
    "write_file": {"fn": write_file, "permission": "write"},
    "list_directory": {"fn": list_directory, "permission": "read"},
    "run_shell": {"fn": run_shell, "permission": "execute"},
    "fetch_url": {"fn": fetch_url, "permission": "read"},
}

def get_tool_fn(name: str):
    """ツール名から関数を取得する"""
    entry = TOOL_REGISTRY.get(name)
    return entry["fn"] if entry else None

def get_tool_names() -> list[str]:
    """ツール名の一覧を返す"""
    return list(TOOL_REGISTRY.keys())

# --- コンテキスト収集（Claude Code MEMORY.md パターン） ---

def build_workspace_context(workspace: str = "/tmp/agent_workspace") -> str:
    """
    作業環境のコンテキストインデックスを構築する。
    Claude CodeのMEMORY.mdと同じ思想：
    軽量なポインタ情報を常にプロンプトに載せる。
    """
    if not os.path.exists(workspace):
        return "作業ディレクトリが存在しません。"

    lines = [f"作業ディレクトリ: {workspace}", ""]

    try:
        entries = os.listdir(workspace)
    except OSError:
        return "作業ディレクトリの読み取りに失敗しました。"

    if not entries:
        lines.append("（ファイルなし）")
        return "\n".join(lines)

    for entry in sorted(entries):
        path = os.path.join(workspace, entry)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            lines.append(f"- {entry} ({size} bytes)")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    preview_lines = []
                    for i, line in enumerate(f):
                        if i >= 5:
                            break
                        preview_lines.append(f"    {line.rstrip()}")
                    lines.append("  プレビュー:")
                    lines.extend(preview_lines)
            except (UnicodeDecodeError, OSError):
                lines.append("  （バイナリファイル）")
        elif os.path.isdir(path):
            lines.append(f"- {entry}/ (ディレクトリ)")

    return "\n".join(lines)
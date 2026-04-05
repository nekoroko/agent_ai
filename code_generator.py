# code_generator.py — 動的コード生成ノード（コンテキスト注入版）
from config import get_llm
from state import AgentState
from tools import build_workspace_context

llm = get_llm(temperature=0.1)

def generate_code(state: AgentState) -> AgentState:
    """
    既存ツールで対応できない場合、
    Gemma 4にPythonコードを生成させる。
    作業環境のコンテキストを必ず渡す。
    """
    current = state["subtasks"][state["current_subtask_index"]]

    # 作業環境のコンテキストを収集
    workspace_context = build_workspace_context()

    prompt = (
        "あなたはPythonコードを生成するアシスタントです。\n"
        "以下のタスクを実行するPythonスクリプトを生成してください。\n\n"
        "## 作業環境の現在の状態\n"
        f"{workspace_context}\n\n"
        "## タスク\n"
        f"{current['description']}\n\n"
        "## 制約\n"
        "- 標準ライブラリのみ使用すること（pip installが必要なライブラリは使わない）\n"
        "- 結果はprint()で標準出力に出すこと\n"
        "- エラーハンドリングを含めること\n"
        "- コードのみを出力すること（説明文は不要）\n"
        "- 作業環境に実在するファイルを使うこと。サンプルデータやダミーデータを自分で作らないこと\n"
        "- ファイルパスは作業環境の情報を参照して正確に指定すること\n\n"
        "Pythonコードのみを出力してください。"
    )

    response = llm.invoke(prompt)
    code = extract_python_code(response.content)

    return {
        **state,
        "generated_code": code,
        "status": "executing"
    }

def extract_python_code(text: str) -> str:
    """レスポンスからPythonコードを抽出する"""
    if "```python" in text:
        code = text.split("```python")[1].split("```")[0]
        return code.strip()
    if "```" in text:
        code = text.split("```")[1].split("```")[0]
        return code.strip()
    return text.strip()

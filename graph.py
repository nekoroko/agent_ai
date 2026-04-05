# graph.py — ReActループベースのエージェント
import re
from langgraph.graph import StateGraph, END
from config import get_llm
from state import AgentState
from tools import get_tool_fn, get_tool_names, build_workspace_context
from sandbox import execute_in_sandbox


def build_system_prompt() -> str:
    """システムプロンプトを構築する"""
    tool_names = get_tool_names()
    workspace = build_workspace_context()

    return (
        "あなたは自律型タスク実行エージェントです。\n"
        "与えられたタスクを、ツールの使用またはPythonコードの生成・実行によって完了させてください。\n\n"
        "## 利用可能なツール\n"
        f"{tool_names}\n"
        "- read_file(path): ファイルを読む\n"
        "- write_file(path, content): ファイルに書く\n"
        "- list_directory(path): ディレクトリ一覧\n"
        "- run_shell(command): シェルコマンド実行\n"
        "- fetch_url(url): URL取得\n\n"
        "## 作業環境\n"
        f"{workspace}\n\n"
        "## 回答形式\n"
        "毎回、以下のいずれかの形式で回答してください。\n\n"
        "ツールを使う場合:\n"
        "THOUGHT: (何をしようとしているか)\n"
        "ACTION: tool_name(引数)\n\n"
        "Pythonコードを生成・実行する場合:\n"
        "THOUGHT: (何をしようとしているか)\n"
        "ACTION: generate_code\n"
        "```python\n"
        "(コード)\n"
        "```\n\n"
        "タスクが完了した場合:\n"
        "THOUGHT: (結果の要約)\n"
        "DONE: (最終結果)\n\n"
        "## 制約\n"
        "- 標準ライブラリのみ使用すること。pandas, numpy等は使用不可\n"
        "- サンプルデータやダミーデータを自分で作らないこと\n"
        "- 作業環境に実在するファイルを使うこと\n"
        "- 結果はprint()で出力すること\n"
    )


def parse_action(text: str) -> dict:
    """LLMの出力からアクションを解析する"""
    # DONEチェック
    done_match = re.search(r"DONE:\s*(.+)", text, re.DOTALL)
    if done_match:
        return {"type": "done", "content": done_match.group(1).strip()}

    # generate_codeチェック
    if "generate_code" in text.lower():
        code_match = re.search(r"```python\s*\n(.+?)```", text, re.DOTALL)
        if code_match:
            return {"type": "code", "content": code_match.group(1).strip()}
        return {"type": "code", "content": ""}

    # ツール呼び出しチェック
    action_match = re.search(r"ACTION:\s*(\w+)\((.+?)\)", text, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        tool_arg = action_match.group(2).strip().strip("'\"")
        return {"type": "tool", "name": tool_name, "arg": tool_arg}

    # どれにもマッチしない場合、コードブロックを探す
    code_match = re.search(r"```python\s*\n(.+?)```", text, re.DOTALL)
    if code_match:
        return {"type": "code", "content": code_match.group(1).strip()}

    return {"type": "unknown", "content": text}


def react_step(state: AgentState) -> AgentState:
    """ReActループの1ステップを実行する"""
    if state["step_count"] >= state["max_steps"]:
        return {**state, "status": "error"}

    llm = get_llm(temperature=0.1)

    # メッセージ構築
    messages = []
    system_prompt = build_system_prompt()
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": f"タスク: {state['task']}"})

    # これまでの履歴を追加
    for entry in state["history"]:
        if entry["role"] == "assistant":
            messages.append({"role": "assistant", "content": entry["content"]})
        elif entry["role"] == "result":
            messages.append({"role": "user", "content": f"実行結果:\n{entry['content']}"})

    # LLM呼び出し
    response = llm.invoke(messages)
    llm_output = response.content

    # アクション解析
    action = parse_action(llm_output)

    # 履歴にLLMの出力を追加
    new_history = state["history"] + [{"role": "assistant", "content": llm_output}]

    # アクション実行
    if action["type"] == "done":
        return {
            **state,
            "history": new_history,
            "status": "done",
            "step_count": state["step_count"] + 1,
        }

    elif action["type"] == "tool":
        tool_fn = get_tool_fn(action.get("name", ""))
        if tool_fn:
            try:
                result = tool_fn(action["arg"])
            except Exception as e:
                result = f"エラー: {e}"
        else:
            result = f"ツール '{action.get('name')}' は存在しません。generate_codeでPythonコードを生成してください。"

        new_history.append({"role": "result", "content": result})
        return {
            **state,
            "history": new_history,
            "status": "running",
            "step_count": state["step_count"] + 1,
        }

    elif action["type"] == "code":
        code = action["content"]
        if not code:
            new_history.append({"role": "result", "content": "コードが空です。Pythonコードブロックを含めてください。"})
            return {
                **state,
                "history": new_history,
                "status": "running",
                "step_count": state["step_count"] + 1,
            }

        result = execute_in_sandbox(code)
        if result["success"]:
            output = result["stdout"] if result["stdout"] else "(出力なし)"
        else:
            output = f"エラー:\n{result['stderr']}"

        new_history.append({"role": "result", "content": output})
        return {
            **state,
            "history": new_history,
            "generated_code": code,
            "status": "running",
            "step_count": state["step_count"] + 1,
        }

    else:
        new_history.append({"role": "result", "content": "回答形式が正しくありません。THOUGHT/ACTION/DONEの形式で回答してください。"})
        return {
            **state,
            "history": new_history,
            "status": "running",
            "step_count": state["step_count"] + 1,
        }


def should_continue(state: AgentState) -> str:
    """ループを続けるか判定する"""
    if state["status"] in ("done", "error"):
        return END
    return "react"


# グラフの構築
workflow = StateGraph(AgentState)
workflow.add_node("react", react_step)
workflow.set_entry_point("react")
workflow.add_conditional_edges("react", should_continue, {"react": "react", END: END})

app = workflow.compile()
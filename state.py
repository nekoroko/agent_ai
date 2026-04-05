# state.py — エージェントの状態定義
from typing import TypedDict, Literal

class AgentState(TypedDict):
    task: str
    history: list[dict]       # {"role": "assistant"|"result", "content": "..."}
    generated_code: str       # 直近の生成コード
    status: Literal["running", "done", "error"]
    step_count: int           # 現在のステップ数
    max_steps: int            # 最大ステップ数
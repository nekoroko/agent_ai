# Gemma 4 自律エージェント

ローカルLLM（Gemma 4 26B-A4B）+ LangGraphで構築した自律エージェント。タスクを渡すと、自分で考えて、ツールを使い、必要ならコードを書いて実行し、結果を返します。

データは一切外部に送信しません。

## 動作環境

| 項目 | 要件 |
|------|------|
| OS | Ubuntu 24.04（VirtualBox VM推奨） |
| Python | 3.12+ |
| GPU | NVIDIA RTX 4060以上（VRAM 8GB+、ホスト側） |
| RAM | 32GB以上（ホスト側） |
| LM Studio | 最新版（ホスト側、Gemma 4モデル読み込み済み） |
| Podman | インストール済み |

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/nekoroko/agent_ai.git
cd agent_ai
```

### 2. Python仮想環境の作成

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 4. Podmanの準備

```bash
# Podmanインストール（Ubuntu）
sudo apt install -y podman

# Pythonイメージを取得（初回のみ）
podman pull docker.io/library/python:3.12-slim
```

### 5. LM Studioの起動（ホスト側）

1. LM StudioでGemma 4 26B-A4Bモデルを読み込む
2. Developerタブで「Start Server」をクリック
3. APIサーバーが `http://localhost:1234` で起動することを確認

### 6. 接続設定の確認

`config.py` の `LM_STUDIO_BASE_URL` を環境に合わせて変更してください。

- VirtualBox VM内から接続する場合: `http://10.0.2.2:1234/v1`（デフォルト）
- 同一マシンで実行する場合: `http://localhost:1234/v1`

### 7. テスト用データの作成

```bash
mkdir -p /tmp/agent_workspace
cat > /tmp/agent_workspace/sales.csv << 'EOF'
month,amount
2026-01,150000
2026-01,80000
2026-02,200000
2026-02,120000
2026-03,180000
2026-03,90000
2026-04,250000
EOF
```

### 8. 実行

```bash
python run.py
```

## タスクの変更

`run.py` の `task` を書き換えるだけで別のタスクを実行できます。

```python
initial_state = {
    "task": "ここにタスクを書く",
    ...
}
```

## ファイル構成

| ファイル | 役割 |
|---------|------|
| config.py | LM Studio接続設定 |
| state.py | エージェントの状態定義 |
| tools.py | ツール群 + パーミッション + コンテキスト収集 |
| sandbox.py | 生成コードのサンドボックス実行（Podman） |
| graph.py | ReActループのグラフ定義（メイン） |
| run.py | 実行スクリプト（進捗表示付き） |

## 関連記事

- [Zenn: Gemma 4で自律エージェントを作る — LangGraph + Podmanで動く全手順](https://zenn.dev/nekoroko/articles/7f22e9c8557aea)

## ライセンス

MIT
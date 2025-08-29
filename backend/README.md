# Bookcast Backend

PDFファイルからポッドキャスト音声を生成するFastAPIベースのバックエンドアプリケーションです。

## 機能

- PDFファイルのアップロード
- AI OCRを使用したテキスト抽出
- ポッドキャスト台本の自動生成
- テキスト音声変換（TTS）
- 音声ファイルの処理・編集

## セットアップ

### 必要な環境

- Python 3.12以上
- UV（Pythonパッケージマネージャー）

### インストール

```bash
# 依存関係をインストール
uv sync

# 開発依存関係も含めてインストール
uv sync --dev
```

### 環境変数

`.env.org` を `.env` にコピーして設定:

## 使用方法

### アプリケーション起動

```bash
# 開発サーバーを起動
uv run fastapi dev src/bookcast/main.py
```

### データベース

```bash
# ローカルデータベースを開始
make db/start

# データベースをリセット
make db/clean
```

## 開発

### テスト

```bash
# 全テストを実行
uv run pytest
# または
make test

# 統合テストを実行
uv run pytest -m integration
# または
make test/integration
```

### コードフォーマット・リント

```bash
# コードフォーマット
uv run ruff format
# または
make format

# リント
uv run ruff check
# または
make lint
```

## アーキテクチャ

### ディレクトリ構成

```
src/bookcast/
├── main.py               # FastAPIアプリケーションエントリーポイント
├── config.py             # 環境設定
├── entities/             # Pydanticモデル（Project, Chapter）
├── repositories          # データアクセス層（Supabase操作）
├── routers/              # APIエンドポイント
├── services/             # ビジネスロジック（OCR、TTS、台本作成など）
├── infrastructure/       # インフラストラクチャ（Google Cloud Storage）
└── internal/             # 内部ワーカー処理
```

### 処理フロー

1. **PDFアップロード**: APIエンドポイント経由でPDFファイルをアップロード
2. **画像変換**: PDFページを画像に変換（`pdf2image`）
3. **テキスト抽出**: Gemini API OCRとLangGraphワークフローでテキスト抽出
4. **台本生成**: AIを使用したポッドキャスト台本の生成
5. **音声変換**: テキスト音声変換と音声処理

### 技術スタック

- **Webフレームワーク**: FastAPI
- **AI処理**: Google Gemini API, LangChain, LangGraph
- **PDF処理**: PyPDF, pdf2image, Pillow
- **データベース**: Supabase
- **音声処理**: Pydub
- **ストレージ**: Google Cloud Storage

## デプロイ

```bash
# サーバーデプロイ
make deploy/server
```

## ライセンス

このプロジェクトのライセンスについては、プロジェクト管理者にお問い合わせください。

# Bookcast Frontend

BookcastはPDFドキュメントをポッドキャスト形式の音声ファイルに変換するStreamlitベースのWebアプリケーションです。PDFのアップロード、チャプター設定、音声生成の進捗監視を行うインターフェースを提供します。

## 機能

- PDFファイルのアップロードとプロジェクト作成
- PDFビューアーでのチャプター境界設定
- OCR → スクリプト → TTS → 音声ファイルの処理パイプライン
- Google Cloud Storageでのファイル管理
- 音声ファイルのダウンロードと再生

## 要件

- Python >= 3.12
- Google Cloud Project (認証設定済み)

## セットアップ

1. **依存関係のインストール**:
   ```bash
   uv sync
   ```

2. **環境設定**:
   `.env.org` を `.env` にコピーして設定:

3. **アプリケーションの起動**:
   ```bash
   uv run streamlit run src/bookcast/app.py
   ```

## 開発コマンド

### 一般的な作業
- **起動**: `uv run streamlit run src/bookcast/app.py`
- **依存関係同期**: `uv sync`
- **リント実行**: `make lint` または `uv run ruff check src tests`
- **フォーマット**: `make format` または `uv run ruff format src tests && uv run ruff check --fix src tests`
- **テスト実行**: `make test` または `uv run pytest tests`
- **統合テスト**: `make test/integration` または `uv run pytest -m integration tests`

## アーキテクチャ

### マルチページStreamlitアプリケーション

アプリケーションはStreamlitのナビゲーションシステムを使用し3つのメインページで構成されます:

1. **プロジェクトページ** (`pages/project.py`): PDFアップロードとプロジェクト作成
2. **チャプター選択ページ** (`pages/select_chapter.py`): チャプター設定用PDFビューアー
3. **ポッドキャストページ** (`pages/podcast.py`): 処理状況と音声ダウンロード

### 主要コンポーネント

- **ビューモデル** (`view_models.py`): データ検証用Pydanticモデル
  - `ProjectViewModel`: プロジェクト状態とチャプター設定の管理
  - `ChapterViewModel`: 個別チャプターの開始/終了ページ管理
- **サービス** (`services/`): ビジネスロジック層
  - `image_file.py`: pdf2imageを使用したPDFから画像への変換
  - `audio_file.py`: 音声ファイル管理とGCS統合
- **セッション状態** (`session_state.py`): Streamlitセッション状態管理
- **設定** (`config.py`): dotenvベースの環境設定

### フロー

1. ユーザーがPDFをアップロード → バックエンドがプロジェクト作成
2. チャプター選択UI用にPDFを画像に変換
3. ユーザーがビジュアルインターフェースでチャプター境界を設定
4. 処理パイプライン: OCR → スクリプト生成 → TTS → 音声編集
5. 最終音声ファイルをGCSに保存しダウンロード可能にする

## バックエンド統合

フロントエンドは別のバックエンドAPIとHTTP通信で連携します。主な統合ポイント:
- プロジェクトの作成と状態ポーリング
- ファイルアップロードと処理調整
- Google Cloud Storageからの音声ファイル取得

## コード標準

- **リンター**: Ruff (E, F, W, I, C9ルール、行長120)
- **テスト**: pytestでunit/integration テストマーカー
- **型ヒント**: 適切な型注釈を使用、`any`/`unknown`を避ける
- **データ検証**: すべてのデータ構造にPydanticモデルを使用
- **エラーハンドリング**: API呼び出しとファイル操作の包括的例外処理

## 依存関係

- **コア**: Streamlit, Pydantic, Requests
- **PDF処理**: pdf2image, Pillow
- **クラウド**: google-cloud-storage
- **設定**: python-dotenv, PyYAML
- **開発ツール**: Ruff (リンター/フォーマッター), pytest, ipython

## 参考情報

このプロジェクトの詳細な実装についてはCLAUDE.mdも参照してください。

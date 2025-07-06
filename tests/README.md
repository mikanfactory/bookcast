# Tests

このディレクトリには bookcast アプリケーションのテストが含まれています。

## 構造

```
tests/
├── __init__.py                  # テストパッケージ
├── conftest.py                  # pytest設定とフィクスチャ
├── test_services.py             # サービス層の単体テスト
├── test_project_integration.py  # プロジェクト処理の統合テスト
├── test_select_chapter.py       # 章選択機能のテスト
└── README.md                    # このファイル
```

## テストの実行

### 全テストを実行
```bash
uv run pytest tests/
```

### 特定のテストファイルを実行
```bash
uv run pytest tests/test_services.py
```

### 詳細な出力で実行
```bash
uv run pytest tests/ -v
```

### カバレッジレポート付きで実行
```bash
uv run pytest tests/ --cov=src/bookcast --cov-report=term-missing
```

### 特定のテストクラスを実行
```bash
uv run pytest tests/test_select_chapter.py::TestSelectChapterPage
```

### 特定のテスト関数を実行
```bash
uv run pytest tests/test_services.py::test_service_manager_initialization
```

## テストの種類

### 単体テスト (`test_services.py`)
- サービス層の個別機能をテスト
- 各サービスクラスの基本機能を検証
- 依存関係の少ない独立したテスト

### 統合テスト (`test_project_integration.py`)
- 複数のサービスが連携する機能をテスト
- 既存データとの互換性を検証
- ファイルシステムとの統合をテスト

### 機能テスト (`test_select_chapter.py`)
- 特定のページ機能をエンドツーエンドでテスト
- UIロジックとサービス層の統合を検証
- エッジケースと異常系をテスト

## フィクスチャ

`conftest.py` で定義されている共通フィクスチャ：

- `service_manager`: グローバルサービスマネージャ
- `sample_filename`: テスト用のファイル名
- `sample_max_pages`: テスト用の最大ページ数
- `clean_session`: クリーンなセッション状態

## テストデータ

テストは既存の `downloads/` ディレクトリ内のデータを使用します：
- `2506.05345.pdf`: メインのテスト用PDF
- 対応する画像・テキストファイル

## 注意事項

- Streamlitの警告は予期されたものです（Streamlitランタイム外でのテスト実行のため）
- 一部のテストは既存データの存在に依存しています
- APIキーが設定されていない場合、一部のテストが失敗する可能性があります
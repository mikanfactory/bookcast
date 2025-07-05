# LLMエージェント化された台本生成システム

このディレクトリには、従来の台本生成システムをLLMエージェント化した新しい実装が含まれています。

## ファイル構成

- `main.py` - メインエントリーポイント
- `agent_models.py` - エージェント用のデータモデル（Topic, Script, QualityReport等）
- `topic_extractor_agent.py` - トピック抽出エージェント
- `script_generator_agent.py` - 台本生成エージェント  
- `script_integrator_agent.py` - 統合・調整エージェント
- `quality_evaluator_agent.py` - 品質評価エージェント
- `script_agent_orchestrator.py` - エージェント統合オーケストレータ
- `simple_test.py` - シンプルなインポートテスト
- `run_test.sh` - テスト実行スクリプト

## 特徴

### エージェント化による改善点

1. **トピック分割**: 長い章を技術的複雑さに基づいて4-6個のトピックに自動分割
2. **品質評価**: 内容網羅性を中心とした自動品質評価と改善提案
3. **自動再生成**: 品質基準を満たすまでの自動リトライ機能
4. **統合調整**: オープニング、トピック間の繋ぎ、クロージングの自動生成

### 処理フロー

1. **トピック抽出**: 元テキストから重要トピックを抽出（技術的複雑さ基準）
2. **台本生成**: 各トピック別に個別台本を生成
3. **統合調整**: 全体の流れを調整し、繋ぎを追加
4. **品質評価**: 内容網羅性を中心に評価・改善提案
5. **自動再生成**: 品質基準未達の場合は自動で再生成

## 使用方法

### 前提条件

1. 必要な依存関係がインストールされていること
   ```bash
   uv install
   ```

2. Gemini API キーが設定されていること
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. 元テキストファイルが適切な場所に配置されていること
   - `downloads/プログラマー脳/texts/page_058.txt` ~ `page_072.txt`

### 実行コマンド

**重要**: 必ずプロジェクトルート（`/Users/shoji/code/bookcast/`）から実行してください

```bash
# プロジェクトルートから実行

# 1. シンプルなインポートテスト
python experiment/simple_test.py

# 2. エージェントシステムのテスト
python experiment/main.py test

# 3. 完全な台本生成
python experiment/main.py agents
# または
python experiment/main.py  # デフォルトはagentsモード
```

**注意**: experimentディレクトリ内から直接実行するとModuleNotFoundErrorが発生します。各ファイルにはプロジェクトルートを自動検出してPYTHONPATHに追加するコードが含まれていますが、プロジェクトルートから実行することを推奨します。

### 便利なスクリプト実行

```bash
# テストスクリプトを実行可能にして実行
chmod +x experiment/run_test.sh
./experiment/run_test.sh
```

## 設定可能なパラメータ

`main.py`内の`AgentConfig`で以下の設定が可能：

- `target_duration_minutes`: 目標時間（デフォルト: 40分）
- `target_topic_count`: 目標トピック数（デフォルト: 5個）
- `topic_duration_range`: トピック時間範囲（デフォルト: 6-10分）
- `quality_threshold`: 品質閾値（デフォルト: 7.0点）
- `max_regeneration_attempts`: 最大再生成回数（デフォルト: 3回）
- `mc1_name/mc2_name`: MC名前（デフォルト: ジェームズ/アリス）

## 出力ファイル

生成された台本は以下の場所に保存されます：

- `downloads/プログラマー脳/scripts/full_script.txt` - 完全な統合台本
- `downloads/プログラマー脳/scripts/topic_01_*.txt` - トピック別台本
- `downloads/プログラマー脳/scripts/quality_report.txt` - 品質評価レポート

## トラブルシューティング

### よくある問題

1. **Import Error**: 
   - PYTHONPATHがプロジェクトルートを含んでいることを確認
   - 必要な依存関係がインストールされていることを確認

2. **API Error**:
   - Gemini API キーが正しく設定されていることを確認
   - ネットワーク接続を確認

3. **File Not Found**:
   - 元テキストファイルが正しい場所にあることを確認
   - ファイルパスが正しいことを確認

### デバッグ

詳細なエラー情報が必要な場合は、`main.py`のテスト関数に詳細なエラーハンドリングが含まれています。

## 従来システムとの比較

| 機能 | 従来システム | エージェント化システム |
|-----|------------|-------------------|
| トピック分割 | 手動 | 自動（技術的複雑さ基準） |
| 品質評価 | なし | 自動評価・改善提案 |
| 再生成 | 手動 | 自動（品質基準未達時） |
| 統合調整 | 基本的 | 高度（オープニング・繋ぎ・クロージング） |
| エラーハンドリング | 基本的 | 包括的リトライ機能 |

エージェント化により、より高品質で一貫性のある台本生成が可能になりました。
import logging
import json
import re
import sys
from pathlib import Path
from typing import List
from google import genai
from google.genai import types

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiment.agent_models import IntegratedScript, QualityReport, Topic, AgentConfig
from bookcast.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


class QualityEvaluatorAgent:
    """台本の品質を評価するエージェント"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def _build_evaluation_prompt(self, original_topics: List[Topic], config: AgentConfig) -> str:
        """品質評価用のプロンプトを構築"""
        key_points_summary = []
        for topic in original_topics:
            key_points_summary.append(f"- {topic.title}: {', '.join(topic.key_points)}")

        return f"""
あなたはポッドキャスト台本の品質評価専門家です。
与えられた台本を多角的に評価し、詳細なレポートを作成してください。

## 評価基準（重要度順）
1. **内容網羅性（最重要）**: 元のトピックの重要ポイントがどの程度カバーされているか
2. **技術的正確性**: 技術的な内容が正確で適切に説明されているか
3. **会話の自然さ**: MC間の対話が自然で魅力的か
4. **時間配分**: 目標時間（{config.target_duration_minutes}分）に適切に収まっているか
5. **全体の流れ**: オープニング、本編、クロージングの構成が適切か

## 元のトピック重要ポイント
{chr(10).join(key_points_summary)}

## 評価指標（各項目0-10点）
- overall_score: 総合評価
- content_coverage: 内容網羅性（最も重要）
- flow_naturalness: 会話の自然さ
- technical_accuracy: 技術的正確性
- time_balance: 時間配分

## 品質判定基準
- 品質閾値: {config.quality_threshold}点
- content_coverage が 7.0 未満の場合は再生成推奨
- overall_score が {config.quality_threshold} 未満の場合は要改善

## 出力形式
以下のJSON形式で評価結果を出力してください：

```json
{{
  "overall_score": 8.5,
  "content_coverage": 9.0,
  "flow_naturalness": 8.0,
  "technical_accuracy": 8.5,
  "time_balance": 8.0,
  "strengths": [
    "重要ポイントが漏れなくカバーされている",
    "技術的説明が正確で詳細"
  ],
  "weaknesses": [
    "一部の会話が不自然",
    "時間配分にやや偏りがある"
  ],
  "suggestions": [
    "MC間の相互作用をより自然にする",
    "各トピックの時間をより均等に配分する"
  ],
  "meets_quality_threshold": true,
  "regeneration_needed": false
}}
```

## 評価の観点
- 元のテキストで重要とされた概念や技術が適切に説明されているか
- 専門用語の使用が適切で、説明が正確か
- MCの性格設定が一貫して反映されているか
- 視聴者の理解を助ける具体例や応用例が含まれているか
- トピック間の繋がりが自然で論理的か
"""

    async def evaluate_script(
        self,
        integrated_script: IntegratedScript,
        original_topics: List[Topic],
        config: AgentConfig
    ) -> QualityReport:
        """統合された台本を評価"""
        try:
            prompt = self._build_evaluation_prompt(original_topics, config)

            # 台本の概要情報を追加
            script_summary = f"""
## 台本情報
- タイトル: {integrated_script.title}
- 総時間: {integrated_script.total_duration:.1f}分
- トピック数: {len(integrated_script.topic_scripts)}個
- 全体の文字数: {len(integrated_script.full_script)}文字

## 評価対象台本
{integrated_script.full_script}
"""

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.3  # 評価は一貫性を重視するため低めに設定
                ),
                contents=script_summary
            )

            response_text = response.text.strip()
            logger.info(f"Raw evaluation response: {response_text[:200]}...")

            # JSON部分を抽出
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("JSON形式の評価結果が見つかりません")

            json_text = response_text[json_start:json_end]
            eval_data = json.loads(json_text)

            # QualityReportオブジェクトを作成
            quality_report = QualityReport(
                overall_score=eval_data["overall_score"],
                content_coverage=eval_data["content_coverage"],
                flow_naturalness=eval_data["flow_naturalness"],
                technical_accuracy=eval_data["technical_accuracy"],
                time_balance=eval_data["time_balance"],
                strengths=eval_data.get("strengths", []),
                weaknesses=eval_data.get("weaknesses", []),
                suggestions=eval_data.get("suggestions", []),
                meets_quality_threshold=eval_data["meets_quality_threshold"],
                regeneration_needed=eval_data["regeneration_needed"]
            )

            logger.info(f"品質評価完了: 総合 {quality_report.overall_score:.1f}点, 網羅性 {quality_report.content_coverage:.1f}点")
            return quality_report

        except Exception as e:
            logger.error(f"品質評価エラー: {e}")
            raise

    def _analyze_content_coverage(self, script: str, original_topics: List[Topic]) -> float:
        """内容網羅性を定量的に分析"""
        total_key_points = 0
        covered_key_points = 0

        for topic in original_topics:
            total_key_points += len(topic.key_points)

            for key_point in topic.key_points:
                # キーポイントに含まれる重要な単語を抽出
                key_words = re.findall(r'\w+', key_point)
                covered = False

                for word in key_words:
                    if len(word) > 2 and word in script:  # 2文字以上の単語が台本に含まれているかチェック
                        covered = True
                        break

                if covered:
                    covered_key_points += 1

        if total_key_points == 0:
            return 10.0

        coverage_ratio = covered_key_points / total_key_points
        return min(coverage_ratio * 10, 10.0)

    def _analyze_dialogue_quality(self, script: str, config: AgentConfig) -> float:
        """会話品質を分析"""
        # MC名の出現回数をチェック
        mc1_count = script.count(f"{config.mc1_name}:")
        mc2_count = script.count(f"{config.mc2_name}:")

        # バランスのチェック（理想的には5:5から7:3の範囲）
        total_dialogues = mc1_count + mc2_count
        if total_dialogues == 0:
            return 0.0

        balance_ratio = min(mc1_count, mc2_count) / max(mc1_count, mc2_count)
        balance_score = balance_ratio * 10

        # 会話の長さのチェック
        dialogue_lines = re.findall(r'^[^:]+:.+$', script, re.MULTILINE)
        if len(dialogue_lines) < 20:  # 最低限の会話数
            return balance_score * 0.5

        return min(balance_score, 10.0)

    def validate_evaluation(self, quality_report: QualityReport, config: AgentConfig) -> bool:
        """評価結果の妥当性をチェック"""
        # スコアが妥当な範囲内かチェック
        scores = [
            quality_report.overall_score,
            quality_report.content_coverage,
            quality_report.flow_naturalness,
            quality_report.technical_accuracy,
            quality_report.time_balance
        ]

        for score in scores:
            if score < 0 or score > 10:
                logger.warning(f"無効なスコア値: {score}")
                return False

        # 論理的整合性のチェック
        if quality_report.meets_quality_threshold and quality_report.overall_score < config.quality_threshold:
            logger.warning("品質閾値の判定に矛盾があります")
            return False

        if quality_report.regeneration_needed and quality_report.overall_score >= config.quality_threshold:
            logger.warning("再生成判定に矛盾があります")
            return False

        return True

    async def generate_improvement_suggestions(
        self,
        quality_report: QualityReport,
        integrated_script: IntegratedScript,
        config: AgentConfig
    ) -> List[str]:
        """品質レポートに基づいて具体的な改善提案を生成"""
        if not quality_report.regeneration_needed:
            return quality_report.suggestions

        try:
            improvement_prompt = f"""
以下の品質評価結果を基に、台本の具体的な改善提案を作成してください。

## 品質評価結果
- 総合評価: {quality_report.overall_score:.1f}点
- 内容網羅性: {quality_report.content_coverage:.1f}点
- 弱点: {', '.join(quality_report.weaknesses)}

## 改善提案の要求
1. 具体的で実行可能な改善策を3-5個提案
2. 最も重要な問題から優先順位をつける
3. 改善によって期待される効果を明記

改善提案をリスト形式で出力してください。
"""

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=improvement_prompt,
                    temperature=0.7
                ),
                contents="具体的な改善提案を作成してください。"
            )

            suggestions_text = response.text.strip()
            suggestions = [line.strip() for line in suggestions_text.split('\n') if line.strip()]

            return suggestions[:5]  # 最大5個まで

        except Exception as e:
            logger.error(f"改善提案生成エラー: {e}")
            return quality_report.suggestions

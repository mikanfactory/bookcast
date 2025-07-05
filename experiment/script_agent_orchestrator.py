import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiment.agent_models import (
    Topic, TopicScript, IntegratedScript, QualityReport,
    AgentConfig, AgentProcessResult
)
from experiment.topic_extractor_agent import TopicExtractorAgent
from experiment.script_generator_agent import ScriptGeneratorAgent
from experiment.script_integrator_agent import ScriptIntegratorAgent
from experiment.quality_evaluator_agent import QualityEvaluatorAgent


logger = logging.getLogger(__name__)


class ScriptAgentOrchestrator:
    """LLMエージェント群を統合し、台本作成ワークフロー全体を管理するオーケストレータ"""

    def __init__(self, api_key: str = None):
        self.topic_extractor = TopicExtractorAgent(api_key)
        self.script_generator = ScriptGeneratorAgent(api_key)
        self.script_integrator = ScriptIntegratorAgent(api_key)
        self.quality_evaluator = QualityEvaluatorAgent(api_key)

    async def create_podcast_script(
        self,
        source_text: str,
        config: Optional[AgentConfig] = None,
        title: str = "技術書籍ポッドキャスト"
    ) -> AgentProcessResult:
        """
        完全なポッドキャスト台本作成ワークフローを実行

        Args:
            source_text: 元のテキスト内容
            config: エージェント設定（Noneの場合はデフォルト設定を使用）
            title: ポッドキャストのタイトル

        Returns:
            AgentProcessResult: 処理結果
        """
        start_time = time.time()

        if config is None:
            config = AgentConfig()

        logger.info(f"台本作成開始: {title}")

        try:
            # フェーズ1: トピック抽出
            topics = await self._extract_topics_with_retry(source_text, config)
            if not topics:
                return AgentProcessResult(
                    success=False,
                    error_message="トピック抽出に失敗しました",
                    processing_time=time.time() - start_time
                )

            # フェーズ2: 品質基準を満たすまで台本生成・統合・評価を繰り返し
            best_result = None
            regeneration_count = 0

            for attempt in range(config.max_regeneration_attempts):
                logger.info(f"台本生成試行 {attempt + 1}/{config.max_regeneration_attempts}")

                try:
                    # 台本生成
                    topic_scripts = await self._generate_scripts_with_retry(topics, config)
                    if not topic_scripts:
                        continue

                    # 台本統合
                    integrated_script = await self._integrate_scripts_with_retry(
                        topic_scripts, config, title
                    )
                    if not integrated_script:
                        continue

                    # 品質評価
                    quality_report = await self._evaluate_quality_with_retry(
                        integrated_script, topics, config
                    )
                    if not quality_report:
                        continue

                    # 現在の結果を記録
                    current_result = AgentProcessResult(
                        success=True,
                        topics=topics,
                        topic_scripts=topic_scripts,
                        integrated_script=integrated_script,
                        quality_report=quality_report,
                        processing_time=time.time() - start_time,
                        regeneration_count=regeneration_count
                    )

                    # 品質基準を満たしているか確認
                    if quality_report.meets_quality_threshold and not quality_report.regeneration_needed:
                        logger.info(f"品質基準を満たす台本が完成しました（試行 {attempt + 1}回目）")
                        return current_result

                    # より良い結果の場合は更新
                    if (best_result is None or
                        quality_report.overall_score > best_result.quality_report.overall_score):
                        best_result = current_result

                    regeneration_count += 1

                except Exception as e:
                    logger.error(f"試行 {attempt + 1} でエラー発生: {e}")
                    continue

            # 最大試行回数に達した場合は最良の結果を返す
            if best_result:
                logger.warning(f"品質基準を満たす台本は作成できませんでしたが、最良の結果を返します")
                best_result.regeneration_count = regeneration_count
                best_result.processing_time = time.time() - start_time
                return best_result

            return AgentProcessResult(
                success=False,
                error_message="品質基準を満たす台本の生成に失敗しました",
                processing_time=time.time() - start_time,
                regeneration_count=regeneration_count
            )

        except Exception as e:
            logger.error(f"台本作成処理中にエラー発生: {e}")
            return AgentProcessResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    async def _extract_topics_with_retry(
        self,
        source_text: str,
        config: AgentConfig,
        max_retries: int = 2
    ) -> Optional[List[Topic]]:
        """リトライ機能付きトピック抽出"""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"トピック抽出試行 {attempt + 1}/{max_retries + 1}")
                topics = await self.topic_extractor.extract_topics(source_text, config)

                if self.topic_extractor.validate_topics(topics, config):
                    logger.info(f"トピック抽出成功: {len(topics)}個のトピック")
                    return topics
                else:
                    logger.warning(f"トピック検証失敗（試行 {attempt + 1}）")

            except Exception as e:
                logger.error(f"トピック抽出エラー（試行 {attempt + 1}）: {e}")

            if attempt < max_retries:
                await asyncio.sleep(1)  # 少し待ってからリトライ

        return None

    async def _generate_scripts_with_retry(
        self,
        topics: List[Topic],
        config: AgentConfig,
        max_retries: int = 2
    ) -> Optional[List[TopicScript]]:
        """リトライ機能付き台本生成"""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"台本生成試行 {attempt + 1}/{max_retries + 1}")
                topic_scripts = await self.script_generator.generate_scripts_for_topics(topics, config)

                # 全てのトピックで台本が生成されたかチェック
                if len(topic_scripts) >= len(topics) * 0.8:  # 80%以上成功していればOK
                    logger.info(f"台本生成成功: {len(topic_scripts)}個の台本")
                    return topic_scripts
                else:
                    logger.warning(f"台本生成の成功率が低い（試行 {attempt + 1}）: {len(topic_scripts)}/{len(topics)}")

            except Exception as e:
                logger.error(f"台本生成エラー（試行 {attempt + 1}）: {e}")

            if attempt < max_retries:
                await asyncio.sleep(1)

        return None

    async def _integrate_scripts_with_retry(
        self,
        topic_scripts: List[TopicScript],
        config: AgentConfig,
        title: str,
        max_retries: int = 2
    ) -> Optional[IntegratedScript]:
        """リトライ機能付き台本統合"""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"台本統合試行 {attempt + 1}/{max_retries + 1}")
                integrated_script = await self.script_integrator.integrate_scripts(
                    topic_scripts, config, title
                )

                if self.script_integrator.validate_integration(integrated_script, config):
                    logger.info("台本統合成功")
                    return integrated_script
                else:
                    logger.warning(f"台本統合検証失敗（試行 {attempt + 1}）")

            except Exception as e:
                logger.error(f"台本統合エラー（試行 {attempt + 1}）: {e}")

            if attempt < max_retries:
                await asyncio.sleep(1)

        return None

    async def _evaluate_quality_with_retry(
        self,
        integrated_script: IntegratedScript,
        topics: List[Topic],
        config: AgentConfig,
        max_retries: int = 2
    ) -> Optional[QualityReport]:
        """リトライ機能付き品質評価"""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"品質評価試行 {attempt + 1}/{max_retries + 1}")
                quality_report = await self.quality_evaluator.evaluate_script(
                    integrated_script, topics, config
                )

                if self.quality_evaluator.validate_evaluation(quality_report, config):
                    logger.info(f"品質評価成功: 総合 {quality_report.overall_score:.1f}点")
                    return quality_report
                else:
                    logger.warning(f"品質評価検証失敗（試行 {attempt + 1}）")

            except Exception as e:
                logger.error(f"品質評価エラー（試行 {attempt + 1}）: {e}")

            if attempt < max_retries:
                await asyncio.sleep(1)

        return None

    def get_processing_summary(self, result: AgentProcessResult) -> str:
        """処理結果の要約を生成"""
        if not result.success:
            return f"処理失敗: {result.error_message}"

        summary_parts = [
            f"処理成功 ({result.processing_time:.1f}秒)",
            f"トピック数: {len(result.topics)}個",
            f"総時間: {result.integrated_script.total_duration:.1f}分",
            f"品質スコア: {result.quality_report.overall_score:.1f}点",
            f"再生成回数: {result.regeneration_count}回"
        ]

        if result.quality_report.meets_quality_threshold:
            summary_parts.append("✅ 品質基準クリア")
        else:
            summary_parts.append("⚠️ 品質基準未達")

        return " | ".join(summary_parts)

    async def quick_test(self, test_text: str = "テストテキスト") -> bool:
        """エージェント統合の簡単な動作テスト"""
        try:
            config = AgentConfig(
                target_duration_minutes=10.0,
                target_topic_count=2,
                max_regeneration_attempts=1
            )

            result = await self.create_podcast_script(test_text, config, "テスト台本")

            if result.success:
                logger.info("クイックテスト成功")
                logger.info(self.get_processing_summary(result))
                return True
            else:
                logger.error(f"クイックテスト失敗: {result.error_message}")
                return False

        except Exception as e:
            logger.error(f"クイックテストエラー: {e}")
            return False

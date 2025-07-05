import logging
import sys
from pathlib import Path
from typing import List
from google import genai
from google.genai import types

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiment.agent_models import TopicScript, IntegratedScript, AgentConfig
from bookcast.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


class ScriptIntegratorAgent:
    """トピック別台本を統合・調整するエージェント"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def _build_opening_prompt(self, topic_scripts: List[TopicScript], config: AgentConfig) -> str:
        """オープニング生成用のプロンプト"""
        topic_titles = [script.topic_title for script in topic_scripts]

        return f"""
あなたはポッドキャスト番組のオープニング作成専門家です。
以下の情報を基に、魅力的なオープニングを作成してください。

## MC設定
- {config.mc1_name}: {config.mc1_personality}
- {config.mc2_name}: {config.mc2_personality}

## 今回のトピック一覧
{chr(10).join(f'- {title}' for title in topic_titles)}

## オープニングの要件
1. 番組への歓迎と挨拶（30秒程度）
2. 今回扱うトピックの概要紹介（1分程度）
3. 視聴者への期待感の醸成（30秒程度）
4. 自然に最初のトピックへの導入

## 出力形式
```
{config.mc1_name}: （挨拶と番組紹介）
{config.mc2_name}: （応答と今回の内容紹介）
{config.mc1_name}: （トピック概要の説明）
{config.mc2_name}: （視聴者への呼びかけと最初のトピックへの導入）
```
"""

    def _build_closing_prompt(self, topic_scripts: List[TopicScript], config: AgentConfig) -> str:
        """クロージング生成用のプロンプト"""
        return f"""
あなたはポッドキャスト番組のクロージング作成専門家です。
今回扱ったトピックを振り返り、魅力的なクロージングを作成してください。

## MC設定
- {config.mc1_name}: {config.mc1_personality}
- {config.mc2_name}: {config.mc2_personality}

## クロージングの要件
1. 今回のトピックの簡潔な振り返り（1分程度）
2. 学んだことの実践的な活用方法（1分程度）
3. 視聴者への感謝と次回予告（30秒程度）
4. 番組終了の挨拶

## 出力形式
```
{config.mc2_name}: （今回のまとめ開始）
{config.mc1_name}: （学習内容の振り返り）
{config.mc2_name}: （実践的な活用方法の提案）
{config.mc1_name}: （視聴者への感謝と次回予告）
{config.mc2_name}: （終了の挨拶）
```
"""

    def _build_transition_prompt(self, from_topic: str, to_topic: str, config: AgentConfig) -> str:
        """トピック間の繋ぎ生成用のプロンプト"""
        return f"""
あなたはポッドキャストの流れを作る専門家です。
以下のトピック間の自然な繋ぎを作成してください。

## MC設定
- {config.mc1_name}: {config.mc1_personality}
- {config.mc2_name}: {config.mc2_personality}

## 繋ぎの情報
- 前のトピック: {from_topic}
- 次のトピック: {to_topic}

## 繋ぎの要件
1. 前のトピックの簡潔なまとめ（15秒程度）
2. 次のトピックへの自然な導入（15秒程度）
3. 2つのトピック間の関連性があれば言及

## 出力形式
```
{config.mc1_name}: （前トピックのまとめと次への導入）
{config.mc2_name}: （次のトピックへの興味を示す発言）
```
"""

    async def generate_opening(self, topic_scripts: List[TopicScript], config: AgentConfig) -> str:
        """オープニングを生成"""
        try:
            prompt = self._build_opening_prompt(topic_scripts, config)

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.7
                ),
                contents="魅力的なオープニングを作成してください。"
            )

            opening = response.text.strip()
            logger.info("オープニング生成完了")
            return opening

        except Exception as e:
            logger.error(f"オープニング生成エラー: {e}")
            raise

    async def generate_closing(self, topic_scripts: List[TopicScript], config: AgentConfig) -> str:
        """クロージングを生成"""
        try:
            prompt = self._build_closing_prompt(topic_scripts, config)

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.7
                ),
                contents="印象的なクロージングを作成してください。"
            )

            closing = response.text.strip()
            logger.info("クロージング生成完了")
            return closing

        except Exception as e:
            logger.error(f"クロージング生成エラー: {e}")
            raise

    async def generate_transitions(self, topic_scripts: List[TopicScript], config: AgentConfig) -> List[str]:
        """トピック間の繋ぎを生成"""
        transitions = []

        try:
            for i in range(len(topic_scripts) - 1):
                from_topic = topic_scripts[i].topic_title
                to_topic = topic_scripts[i + 1].topic_title

                prompt = self._build_transition_prompt(from_topic, to_topic, config)

                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    config=types.GenerateContentConfig(
                        system_instruction=prompt,
                        temperature=0.7
                    ),
                    contents=f"{from_topic}から{to_topic}への自然な繋ぎを作成してください。"
                )

                transition = response.text.strip()
                transitions.append(transition)

            logger.info(f"繋ぎ生成完了: {len(transitions)}個")
            return transitions

        except Exception as e:
            logger.error(f"繋ぎ生成エラー: {e}")
            raise

    async def integrate_scripts(
        self,
        topic_scripts: List[TopicScript],
        config: AgentConfig,
        title: str = "技術書籍ポッドキャスト"
    ) -> IntegratedScript:
        """台本を統合"""
        try:
            # 並列で各パーツを生成
            opening_task = self.generate_opening(topic_scripts, config)
            closing_task = self.generate_closing(topic_scripts, config)
            transitions_task = self.generate_transitions(topic_scripts, config)

            opening = await opening_task
            closing = await closing_task
            transitions = await transitions_task

            # 完全な台本を構築
            full_script_parts = [opening]

            for i, script in enumerate(topic_scripts):
                full_script_parts.append(f"\n\n=== {script.topic_title} ===\n")
                full_script_parts.append(script.script_content)

                # 最後のトピック以外には繋ぎを追加
                if i < len(topic_scripts) - 1:
                    full_script_parts.append(f"\n\n--- 繋ぎ {i+1} ---\n")
                    full_script_parts.append(transitions[i])

            full_script_parts.append(f"\n\n=== クロージング ===\n")
            full_script_parts.append(closing)

            full_script = "".join(full_script_parts)
            total_duration = sum(script.estimated_duration for script in topic_scripts) + 4.0  # オープニング・クロージング分

            integrated_script = IntegratedScript(
                title=title,
                total_duration=total_duration,
                topic_scripts=topic_scripts,
                transitions=transitions,
                opening=opening,
                closing=closing,
                full_script=full_script
            )

            logger.info(f"台本統合完了: 総時間 {total_duration:.1f}分")
            return integrated_script

        except Exception as e:
            logger.error(f"台本統合エラー: {e}")
            raise

    def validate_integration(self, integrated_script: IntegratedScript, config: AgentConfig) -> bool:
        """統合された台本の妥当性をチェック"""
        # 時間の妥当性チェック
        if integrated_script.total_duration < config.target_duration_minutes * 0.8:
            logger.warning(f"総時間が短すぎます: {integrated_script.total_duration:.1f}分")
            return False

        if integrated_script.total_duration > config.target_duration_minutes * 1.3:
            logger.warning(f"総時間が長すぎます: {integrated_script.total_duration:.1f}分")
            return False

        # 必要な要素が含まれているかチェック
        if not integrated_script.opening or len(integrated_script.opening) < 50:
            logger.warning("オープニングが不適切です")
            return False

        if not integrated_script.closing or len(integrated_script.closing) < 50:
            logger.warning("クロージングが不適切です")
            return False

        expected_transitions = len(integrated_script.topic_scripts) - 1
        if len(integrated_script.transitions) != expected_transitions:
            logger.warning(f"繋ぎの数が不正です: {len(integrated_script.transitions)} (期待値: {expected_transitions})")
            return False

        return True

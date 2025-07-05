import logging
import re
import sys
from pathlib import Path
from typing import List
from google import genai
from google.genai import types

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiment.agent_models import Topic, TopicScript, AgentConfig
from bookcast.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


class ScriptGeneratorAgent:
    """トピック別の台本を生成するエージェント"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def _build_script_prompt(self, topic: Topic, config: AgentConfig) -> str:
        """台本生成用のプロンプトを構築"""
        return f"""
あなたはポッドキャスト台本作成の専門家です。与えられたトピックに基づいて、自然で魅力的な台本を作成してください。

## MC設定
- {config.mc1_name}: {config.mc1_personality}な人物
- {config.mc2_name}: {config.mc2_personality}な人物

## トピック情報
- タイトル: {topic.title}
- 説明: {topic.description}
- 目標時間: {topic.estimated_minutes}分
- 重要ポイント: {', '.join(topic.key_points)}
- 複雑さレベル: {topic.complexity_score}/10

## 台本作成ガイドライン
1. **導入部**: トピックを紹介し、なぜ重要なのかを説明（1-2分）
2. **主要内容**: 重要ポイントを会話形式で深く掘り下げ（4-6分）
3. **まとめ**: 学んだことを整理し、実践的な示唆を提供（1-2分）

## 会話スタイル
- 視聴者は専門知識を持っているため、技術的な内容をそのまま扱う
- 難しい概念も簡略化せず、正確に説明する
- {config.mc1_name}は深い洞察と慎重な分析を提供
- {config.mc2_name}は具体例や実践的な応用例を積極的に提案
- 自然な相互作用と質問・回答の流れを作る

## 出力形式
以下の形式で台本を作成してください：

```
=== {topic.title} ===

[導入部]
{config.mc1_name}: （導入の発言）
{config.mc2_name}: （応答・補足）

[主要内容]
{config.mc1_name}: （主要ポイント1の説明）
{config.mc2_name}: （質問や具体例の提案）
{config.mc1_name}: （詳細説明や分析）
（中略）

[まとめ]
{config.mc2_name}: （まとめの開始）
{config.mc1_name}: （総括と今後の示唆）
```

## 注意事項
- 与えられた元テキストの内容を忠実に反映する
- 技術的正確性を保つ
- 会話が自然で魅力的になるよう工夫する
- 目標時間内に収まるよう調整する
"""

    async def generate_script(self, topic: Topic, config: AgentConfig) -> TopicScript:
        """トピックから台本を生成"""
        try:
            prompt = self._build_script_prompt(topic, config)

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.8
                ),
                contents=f"以下の内容を基に台本を作成してください：\n\n{topic.source_text}"
            )

            script_content = response.text.strip()

            # 会話回数を数える（発言の数）
            dialogue_count = len(re.findall(r'^[^:]+:', script_content, re.MULTILINE))

            # 実際の時間を推定（平均的な読み上げ速度を考慮）
            char_count = len(script_content)
            estimated_duration = self._estimate_duration(char_count)

            topic_script = TopicScript(
                topic_id=topic.id,
                topic_title=topic.title,
                script_content=script_content,
                estimated_duration=estimated_duration,
                dialogue_count=dialogue_count
            )

            logger.info(f"台本生成完了: {topic.title} ({estimated_duration:.1f}分, {dialogue_count}回の会話)")
            return topic_script

        except Exception as e:
            logger.error(f"台本生成エラー - {topic.title}: {e}")
            raise

    async def generate_scripts_for_topics(self, topics: List[Topic], config: AgentConfig) -> List[TopicScript]:
        """複数のトピックに対して台本を生成"""
        scripts = []

        for topic in topics:
            try:
                script = await self.generate_script(topic, config)
                scripts.append(script)
            except Exception as e:
                logger.error(f"トピック {topic.title} の台本生成に失敗: {e}")
                # エラーが発生しても他のトピックの処理を続行
                continue

        total_duration = sum(script.estimated_duration for script in scripts)
        logger.info(f"全台本生成完了: {len(scripts)}個, 総時間 {total_duration:.1f}分")

        return scripts

    def _estimate_duration(self, char_count: int) -> float:
        """文字数から推定再生時間を計算"""
        # 日本語の平均的な読み上げ速度: 約300文字/分
        # ポッドキャストでは少し余裕を持って250文字/分で計算
        chars_per_minute = 250
        return char_count / chars_per_minute

    def validate_script(self, script: TopicScript, target_duration: float, tolerance: float = 0.3) -> bool:
        """生成された台本の妥当性をチェック"""
        # 時間の妥当性チェック
        duration_diff = abs(script.estimated_duration - target_duration)
        if duration_diff > target_duration * tolerance:
            logger.warning(f"時間が目標から大きく外れています: {script.estimated_duration:.1f}分 (目標: {target_duration:.1f}分)")
            return False

        # 会話回数のチェック（最低限の対話があるか）
        if script.dialogue_count < 6:
            logger.warning(f"会話回数が少なすぎます: {script.dialogue_count}回")
            return False

        # 内容の長さチェック
        if len(script.script_content) < 100:
            logger.warning("台本が短すぎます")
            return False

        return True

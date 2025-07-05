import json
import logging
import sys
from pathlib import Path
from typing import List
from google import genai
from google.genai import types

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiment.agent_models import Topic, AgentConfig
from bookcast.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


class TopicExtractorAgent:
    """技術的複雑さを基準にトピックを抽出するエージェント"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def _build_extraction_prompt(self, config: AgentConfig) -> str:
        """トピック抽出用のプロンプトを構築"""
        return f"""
あなたは技術書籍の内容分析専門家です。与えられたテキストから、ポッドキャスト用のトピックを抽出してください。

## 抽出条件
- トピック数: {config.target_topic_count}個（4-6個の範囲）
- 各トピックの時間: {config.topic_duration_range[0]}-{config.topic_duration_range[1]}分
- 選定基準: 技術的複雑さの高いものを優先
- 全体の目標時間: {config.target_duration_minutes}分

## 出力形式
以下のJSON形式で出力してください：

```json
{{
  "topics": [
    {{
      "id": 1,
      "title": "トピックのタイトル",
      "description": "トピックの詳細説明（2-3文）",
      "complexity_score": 8.5,
      "estimated_minutes": 7.5,
      "key_points": ["重要ポイント1", "重要ポイント2", "重要ポイント3"],
      "source_text": "該当する元テキストの抜粋"
    }}
  ]
}}
```

## 評価基準
- complexity_score: 技術的複雑さを0-10で評価（高いほど複雑）
- 概念の抽象度、実装の難易度、理解に必要な前提知識などを総合評価
- プログラミング、アルゴリズム、システム設計などの技術要素を重視

## 注意事項
- トピック間の重複を避ける
- 各トピックが独立して理解できるようにする
- key_pointsは3-5個程度にまとめる
- source_textは重要な部分を300-500文字程度で抜粋
"""

    async def extract_topics(self, source_text: str, config: AgentConfig) -> List[Topic]:
        """テキストからトピックを抽出"""
        try:
            prompt = self._build_extraction_prompt(config)

            response = await self.client.aio.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.7
                ),
                contents=f"以下のテキストを分析してください：\n\n{source_text}"
            )

            response_text = response.text.strip()
            logger.info(f"Raw response: {response_text}")

            # JSON部分を抽出
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("JSON形式の応答が見つかりません")

            json_text = response_text[json_start:json_end]
            parsed_data = json.loads(json_text)

            topics = []
            for i, topic_data in enumerate(parsed_data.get("topics", [])):
                topic = Topic(
                    id=i + 1,
                    title=topic_data["title"],
                    description=topic_data["description"],
                    complexity_score=topic_data["complexity_score"],
                    estimated_minutes=topic_data["estimated_minutes"],
                    key_points=topic_data.get("key_points", []),
                    source_text=topic_data["source_text"]
                )
                topics.append(topic)

            # トピック数の調整
            if len(topics) < config.target_topic_count - 1:
                logger.warning(f"抽出されたトピック数が少なすぎます: {len(topics)}")
            elif len(topics) > config.target_topic_count + 1:
                # 複雑さスコアの高い順にソートして上位を選択
                topics.sort(key=lambda t: t.complexity_score, reverse=True)
                topics = topics[:config.target_topic_count]
                logger.info(f"トピック数を{config.target_topic_count}個に調整しました")

            # 時間配分の調整
            total_time = sum(t.estimated_minutes for t in topics)
            if total_time > config.target_duration_minutes:
                adjustment_ratio = config.target_duration_minutes / total_time
                for topic in topics:
                    topic.estimated_minutes *= adjustment_ratio

            logger.info(f"抽出完了: {len(topics)}個のトピック")
            return topics

        except Exception as e:
            logger.error(f"トピック抽出エラー: {e}")
            raise

    def validate_topics(self, topics: List[Topic], config: AgentConfig) -> bool:
        """抽出されたトピックの妥当性をチェック"""
        if not topics:
            return False

        if len(topics) < 4 or len(topics) > 6:
            logger.warning(f"トピック数が範囲外: {len(topics)}")
            return False

        total_time = sum(t.estimated_minutes for t in topics)
        if total_time < config.target_duration_minutes * 0.8 or total_time > config.target_duration_minutes * 1.2:
            logger.warning(f"総時間が範囲外: {total_time}分")
            return False

        # 複雑さスコアの妥当性チェック
        avg_complexity = sum(t.complexity_score for t in topics) / len(topics)
        if avg_complexity < 5.0:
            logger.warning(f"平均複雑さスコアが低すぎます: {avg_complexity}")
            return False

        return True

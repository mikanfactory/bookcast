from typing import List, Optional
from pydantic import BaseModel, Field


class Topic(BaseModel):
    """抽出されたトピック情報"""
    id: int
    title: str
    description: str
    complexity_score: float = Field(ge=0, le=10, description="技術的複雑さスコア（0-10）")
    estimated_minutes: float = Field(default=8.0, description="推定所要時間（分）")
    key_points: List[str] = Field(default_factory=list, description="重要なポイント")
    source_text: str = Field(description="元のテキスト内容")


class TopicScript(BaseModel):
    """トピック別の台本"""
    topic_id: int
    topic_title: str
    script_content: str
    estimated_duration: float = Field(description="推定再生時間（分）")
    dialogue_count: int = Field(description="会話回数")


class IntegratedScript(BaseModel):
    """統合された最終台本"""
    title: str
    total_duration: float
    topic_scripts: List[TopicScript]
    transitions: List[str] = Field(default_factory=list, description="トピック間の繋ぎ")
    opening: str = Field(default="", description="オープニング")
    closing: str = Field(default="", description="クロージング")
    full_script: str = Field(description="完全な台本")


class QualityReport(BaseModel):
    """品質評価レポート"""
    overall_score: float = Field(ge=0, le=10, description="総合評価スコア")
    content_coverage: float = Field(ge=0, le=10, description="内容網羅性スコア")
    flow_naturalness: float = Field(ge=0, le=10, description="会話の自然さスコア")
    technical_accuracy: float = Field(ge=0, le=10, description="技術的正確性スコア")
    time_balance: float = Field(ge=0, le=10, description="時間配分スコア")
    
    strengths: List[str] = Field(default_factory=list, description="良い点")
    weaknesses: List[str] = Field(default_factory=list, description="改善点")
    suggestions: List[str] = Field(default_factory=list, description="改善提案")
    
    meets_quality_threshold: bool = Field(description="品質基準を満たしているか")
    regeneration_needed: bool = Field(description="再生成が必要か")


class AgentConfig(BaseModel):
    """エージェント設定"""
    target_duration_minutes: float = Field(default=40.0, description="目標時間（分）")
    target_topic_count: int = Field(default=5, description="目標トピック数")
    topic_duration_range: tuple[float, float] = Field(default=(6.0, 10.0), description="トピック時間範囲")
    quality_threshold: float = Field(default=7.0, description="品質閾値")
    max_regeneration_attempts: int = Field(default=3, description="最大再生成回数")
    
    mc1_name: str = Field(default="ジェームズ", description="MC1の名前")
    mc2_name: str = Field(default="アリス", description="MC2の名前")
    mc1_personality: str = Field(default="穏やかで思慮深い", description="MC1の性格")
    mc2_personality: str = Field(default="元気で明るい", description="MC2の性格")


class AgentProcessResult(BaseModel):
    """エージェント処理結果"""
    success: bool
    topics: List[Topic] = Field(default_factory=list)
    topic_scripts: List[TopicScript] = Field(default_factory=list)
    integrated_script: Optional[IntegratedScript] = None
    quality_report: Optional[QualityReport] = None
    error_message: Optional[str] = None
    processing_time: float = Field(default=0.0, description="処理時間（秒）")
    regeneration_count: int = Field(default=0, description="再生成回数")
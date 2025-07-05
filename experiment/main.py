import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_text_directory,
    build_script_directory,
)


SCRIPT_WRITING_MODEL = "gemini-2.0-flash"
logger = logging.getLogger(__name__)

# New agent-based imports
from experiment.agent_models import AgentConfig, AgentProcessResult
from experiment.script_agent_orchestrator import ScriptAgentOrchestrator

class AgentBasedScriptWriter:
    """新しいエージェントベースの台本生成クラス"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.orchestrator = ScriptAgentOrchestrator(api_key)
        self.api_key = api_key

    async def generate_script_with_agents(
            self,
            filename: str,
            source_text: str,
            config: AgentConfig = None,
            title: str = None
    ) -> AgentProcessResult:
        """エージェントを使用して高品質な台本を生成"""
        if config is None:
            config = AgentConfig()

        if title is None:
            title = f"{filename} ポッドキャスト"

        logger.info(f"エージェントベース台本生成開始: {filename}")

        # エージェントオーケストレータで台本生成
        result = await self.orchestrator.create_podcast_script(
            source_text=source_text,
            config=config,
            title=title
        )

        if result.success:
            # 生成された台本をファイルに保存
            await self._save_agent_results(filename, result)
            logger.info(f"エージェントベース台本生成完了: {filename}")
            logger.info(self.orchestrator.get_processing_summary(result))
        else:
            logger.error(f"エージェントベース台本生成失敗: {result.error_message}")

        return result

    async def _save_agent_results(self, filename: str, result: AgentProcessResult):
        """エージェント生成結果をファイルに保存"""
        script_dir = build_script_directory(filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        # 統合された完全な台本を保存
        full_script_path = script_dir / "full_script.txt"
        with open(full_script_path, "w", encoding="utf-8") as f:
            f.write(result.integrated_script.full_script)

        # トピック別台本も個別に保存
        for i, topic_script in enumerate(result.topic_scripts):
            topic_script_path = script_dir / f"topic_{i+1:02d}_{topic_script.topic_title.replace('/', '_')}.txt"
            with open(topic_script_path, "w", encoding="utf-8") as f:
                f.write(topic_script.script_content)

        # 品質レポートを保存
        report_path = script_dir / "quality_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"品質評価レポート\n")
            f.write(f"="*50 + "\n")
            f.write(f"総合評価: {result.quality_report.overall_score:.1f}点\n")
            f.write(f"内容網羅性: {result.quality_report.content_coverage:.1f}点\n")
            f.write(f"会話の自然さ: {result.quality_report.flow_naturalness:.1f}点\n")
            f.write(f"技術的正確性: {result.quality_report.technical_accuracy:.1f}点\n")
            f.write(f"時間配分: {result.quality_report.time_balance:.1f}点\n")
            f.write(f"\n良い点:\n")
            for strength in result.quality_report.strengths:
                f.write(f"- {strength}\n")
            f.write(f"\n改善点:\n")
            for weakness in result.quality_report.weaknesses:
                f.write(f"- {weakness}\n")
            f.write(f"\n改善提案:\n")
            for suggestion in result.quality_report.suggestions:
                f.write(f"- {suggestion}\n")

        logger.info(f"エージェント結果保存完了: {script_dir}")

    async def quick_test(self) -> bool:
        """エージェントシステムの簡単なテスト"""
        return await self.orchestrator.quick_test()


async def __generate_script_with_agents():
    """新しいエージェントベース台本生成"""
    filename = "プログラマー脳.pdf"
    start_page, end_page = 58, 72

    text_dir = build_text_directory(filename)

    # テキストを結合
    source_text = "文章は「プログラマー脳」の第3章です。\n"
    for page_num in range(start_page, end_page + 1):
        text_path = text_dir / f"page_{page_num:03d}.txt"
        if text_path.exists():
            with open(text_path, "r", encoding="utf-8") as f:
                source_text += f.read() + "\n"

    # エージェント設定
    config = AgentConfig(
        target_duration_minutes=40.0,
        target_topic_count=5,
        topic_duration_range=(6.0, 10.0),
        quality_threshold=7.0,
        max_regeneration_attempts=3,
        mc1_name="ジェームズ",
        mc2_name="アリス",
        mc1_personality="穏やかで思慮深い",
        mc2_personality="元気で明るい"
    )

    # エージェントベース台本生成
    writer = AgentBasedScriptWriter()
    result = await writer.generate_script_with_agents(
        filename=filename,
        source_text=source_text,
        config=config,
        title="プログラマー脳 第3章 ポッドキャスト"
    )

    if result.success:
        print("\n" + "="*60)
        print("🎉 エージェントベース台本生成が完了しました！")
        print("="*60)
        print(writer.orchestrator.get_processing_summary(result))
        print("\n📊 品質レポート:")
        print(f"   総合評価: {result.quality_report.overall_score:.1f}点")
        print(f"   内容網羅性: {result.quality_report.content_coverage:.1f}点")
        print(f"   会話の自然さ: {result.quality_report.flow_naturalness:.1f}点")
        print(f"   技術的正確性: {result.quality_report.technical_accuracy:.1f}点")
        print(f"   時間配分: {result.quality_report.time_balance:.1f}点")

        if result.quality_report.meets_quality_threshold:
            print("✅ 品質基準をクリアしています")
        else:
            print("⚠️ 品質基準を満たしていません")

        print(f"\n📁 生成ファイル:")
        script_dir = build_script_directory(filename)
        print(f"   完全な台本: {script_dir}/full_script.txt")
        print(f"   品質レポート: {script_dir}/quality_report.txt")
        print(f"   トピック別台本: {script_dir}/topic_*.txt")

    else:
        print(f"❌ 台本生成に失敗しました: {result.error_message}")


async def test_agents():
    """エージェントシステムのテスト"""
    print("🧪 エージェントシステムテスト開始...")

    try:
        print("📦 Creating AgentBasedScriptWriter...")
        writer = AgentBasedScriptWriter()
        print("✅ AgentBasedScriptWriter created successfully")
        
        print("🔍 Running quick test...")
        success = await writer.quick_test()

        if success:
            print("✅ エージェントシステムテスト成功")
        else:
            print("❌ エージェントシステムテスト失敗")

        return success
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   必要なモジュールがインストールされていない可能性があります")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン実行関数"""
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "test":
            asyncio.run(test_agents())
        elif mode == "agents":
            asyncio.run(__generate_script_with_agents())
        else:
            print("使用方法:")
            print("  python main.py [test|agents]")
            print("    test: エージェントシステムテスト")
            print("    agents: 新しいエージェントベース台本生成（デフォルト）")
    else:
        # デフォルトは新しいエージェントベース台本生成
        asyncio.run(__generate_script_with_agents())


if __name__ == "__main__":
    main()

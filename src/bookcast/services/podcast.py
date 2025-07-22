import asyncio
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from bookcast.config import GEMINI_API_KEY
from bookcast.models import Chapters, PodcastSetting
from bookcast.path_resolver import (
    build_script_directory,
    build_text_directory,
    resolve_script_path,
)
from bookcast.services.base import BaseService, ServiceResult


class PodCastScriptWriter(object):
    def __init__(self, llm):
        self.llm = llm


class PodCastScriptEvaluator(object):
    def __init__(self, llm):
        self.llm = llm


class PodCastOrchestrator(object):
    def __init__(self, llm):
        self.llm = llm


class Chapter(BaseModel):
    filename: str = Field(...)
    chapter_number: int = Field(...)
    extracted_texts: List[str] = Field(...)

    @property
    def text(self) -> str:
        acc = ""
        for t in self.extracted_texts:
            acc += t
            acc += "\n\n"

        return acc


def _build_script_prompt(podcast_setting: PodcastSetting) -> str:
    base_prompt = (
        "与えられた文章をもとに、ポッドキャストの台本を作成してください。"
        f"ポッドキャストのMCは{podcast_setting.num_of_people}人います。"
    )

    if podcast_setting.num_of_people >= 1:
        base_prompt += f"1人目の名前は「{podcast_setting.personality1_name}」です。"

    if podcast_setting.num_of_people >= 2:
        base_prompt += f"2人目の名前は「{podcast_setting.personality2_name}」です。"

    base_prompt += (
        "扱うトピックは難しいですが、視聴者は専門知識を持っているため、難しいまま理解できます。"
        "与えられた文章をなるべく端折らず、会話で掘り下げていく形で台本を作成してください。"
        f"ポッドキャストの長さは約{podcast_setting.length}分です。"
    )

    if podcast_setting.prompt:
        base_prompt += f"\n\n追加の指示: {podcast_setting.prompt}"

    return base_prompt


class PodcastService(BaseService):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.semaphore = asyncio.Semaphore(10)
        self.script_model = "gemini-2.0-flash"

    async def _generate_script_for_text(self, text: str, prompt: str) -> str:
        response = self.gemini_client.aio.models.generate_content(
            model=self.script_model,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=text,
        )

        resp = await response
        return resp.text.strip()

    async def _generate_chapter_script(self, chapter: Chapter, prompt: str) -> str:
        async with self.semaphore:
            script = await self._generate_script_for_text(chapter.text, prompt)

        script_dir = build_script_directory(chapter.filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        script_path = resolve_script_path(chapter.filename, chapter.chapter_number)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        return script

    def process(self, podcast_setting: PodcastSetting, chapter: Chapter):
        prompt = _build_script_prompt(podcast_setting)
        asyncio.run(self._generate_chapter_script(chapter, prompt))

    # @staticmethod
    # def _get_chapter_page_ranges(chapters: Chapters, max_page_number: int) -> List[tuple]:
    #     chapter_pages = []
    #     for config in chapters.chapters.values():
    #         chapter_pages.append(config.page_number)
    #
    #     chapter_pages.sort()
    #
    #     ranges = []
    #     for i, start_page in enumerate(chapter_pages):
    #         if i < len(chapter_pages) - 1:
    #             end_page = chapter_pages[i + 1] - 1
    #         else:
    #             end_page = max_page_number
    #
    #         ranges.append((start_page, end_page))
    #
    #     return ranges
    #
    # @staticmethod
    # def _combine_chapter_text(filename: str, start_page: int, end_page: int) -> str:
    #     text_dir = build_text_directory(filename)
    #     combined_text = ""
    #
    #     for page_num in range(start_page, end_page + 1):
    #         text_path = text_dir / f"page_{page_num:03d}.txt"
    #         if text_path.exists():
    #             with open(text_path, "r", encoding="utf-8") as f:
    #                 combined_text += f.read() + "\n"
    #
    #     return combined_text
    #
    # async def generate_podcast_scripts(
    #     self,
    #     filename: str,
    #     max_page_number: int,
    #     chapters: Chapters,
    #     podcast_setting: PodcastSetting,
    # ) -> ServiceResult:
    #     self._log_info(
    #         f"Generating podcast scripts for {len(chapters.chapters)} chapters"
    #     )
    #
    #     prompt = self._build_script_prompt(podcast_setting)
    #
    #     page_ranges = self._get_chapter_page_ranges(chapters, max_page_number)
    #
    #     # Combine text for each chapter
    #     chapter_texts = []
    #     for start_page, end_page in page_ranges:
    #         text = self._combine_chapter_text(filename, start_page, end_page)
    #         chapter_texts.append(text)
    #
    #     tasks = []
    #     for chapter_num, text in enumerate(chapter_texts, 1):
    #         task = self._generate_and_save_script(
    #             filename, chapter_num, text, prompt
    #         )
    #         tasks.append(task)
    #
    #     scripts = await asyncio.gather(*tasks)
    #
    #     combined_script = "\n\n--- 次の章 ---\n\n".join(scripts)
    #
    #     result = {
    #         "scripts": scripts,
    #         "combined_script": combined_script,
    #         "chapters_processed": len(scripts),
    #         "prompt_used": prompt,
    #     }
    #
    #     self._log_info(f"Successfully generated {len(scripts)} scripts")
    #     return ServiceResult.success(result)
    #
    # @staticmethod
    # def get_script_content(filename: str, chapter_num: int) -> ServiceResult:
    #     script_path = resolve_script_path(filename, chapter_num)
    #
    #     if not script_path.exists():
    #         return ServiceResult.failure(
    #             f"Script file not found for chapter {chapter_num}"
    #         )
    #
    #     with open(script_path, "r", encoding="utf-8") as f:
    #         content = f.read()
    #
    #     result = {
    #         "chapter_num": chapter_num,
    #         "content": content,
    #         "file_path": str(script_path),
    #     }
    #
    #     return ServiceResult.success(result)
    #
    # def get_all_scripts(self, filename: str, chapters: Chapters) -> ServiceResult:
    #     self._log_info(f"Getting all scripts for {len(chapters.chapters)} chapters")
    #
    #     scripts = []
    #     for chapter_num in sorted(chapters.chapters.keys()):
    #         script_result = self.get_script_content(filename, chapter_num)
    #         if script_result.success:
    #             scripts.append(script_result.data)
    #         else:
    #             self._log_error(
    #                 f"Failed to get script for chapter {chapter_num}: "
    #                 f"{script_result.error}"
    #             )
    #
    #     # Combine all scripts
    #     combined_content = "\n\n--- 次の章 ---\n\n".join(
    #         [s["content"] for s in scripts]
    #     )
    #
    #     result = {
    #         "scripts": scripts,
    #         "combined_content": combined_content,
    #         "total_chapters": len(scripts),
    #     }

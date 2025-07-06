import logging
import asyncio
from itertools import pairwise


from google import genai
from google.genai import types

from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_text_directory,
    build_script_directory,
    resolve_script_path,
)
from bookcast.models import Chapters, PodcastSetting


SCRIPT_WRITING_MODEL = "gemini-2.0-flash"

logger = logging.getLogger(__name__)


class GeminiScriptWriter:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.semaphore = asyncio.Semaphore(10)

    async def generate(self, base_text: str, prompt: str) -> str:
        response = self.client.aio.models.generate_content(
            model=SCRIPT_WRITING_MODEL,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=base_text,
        )
        resp = await response
        return resp.text.strip()

    async def generate_script(
        self, filename: str, chapter_num: int, base_text: str, prompt: str
    ) -> str:
        async with self.semaphore:
            script = await self.generate(base_text, prompt)

        script_dir = build_script_directory(filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        script_path = resolve_script_path(filename, chapter_num)
        with open(script_path, "w") as f:
            f.write(script)

        return script


def resolve_chapter_min_max_page(
    max_page_number: int, chapters: Chapters
) -> list[list[int]]:
    acc = []
    for config in chapters.chapters.values():
        acc.append(config.page_number)

    pairs = [list(t) for t in pairwise(acc)]
    pairs += [pairs[-1][-1], max_page_number]
    return pairs


def build_prompt() -> str:
    prompt = (
        "与えられた文章をもとに、ポッドキャストの台本を作成してください。"
        "ポッドキャストのMCは2人います。1人目の名前は「ジェームズ」で、穏やかで思慮深い人物です。"
        "2人目の名前は「アリス」で、元気で明るい人物です。"
        "扱うトピックは難しいですが、視聴者は専門知識を持っているため、難しいまま理解できます。"
        "与えられた文章をなるべく端折らず、会話で掘り下げていく形で台本を作成してください。"
        "ポッドキャストの長さは約40分です。"
    )
    return prompt


async def combine(
    filename: str, base_texts: list[str], podcast_setting: PodcastSetting
):
    writer = GeminiScriptWriter(GEMINI_API_KEY)

    prompt = build_prompt()

    tasks = []
    for n, base_text in enumerate(base_texts):
        chapter_num = n + 1
        tasks.append(writer.generate_script(filename, chapter_num, base_text, prompt))

    await asyncio.gather(*tasks)


async def generate_script(
    filename: str,
    max_page_number: int,
    chapters: Chapters,
    podcast_setting: PodcastSetting,
):
    base_texts = []

    text_dir = build_text_directory(filename)
    pairs = resolve_chapter_min_max_page(max_page_number, chapters)
    for pair in pairs:
        start_page, end_page = pair
        text = ""
        for page_num in range(start_page, end_page + 1):
            text_path = text_dir / f"page_{page_num:03d}.txt"
            with open(text_path, "r", encoding="utf-8") as f:
                text += f.read() + "\n"

        base_texts.append(text)

    asyncio.run(combine(filename, base_texts, podcast_setting))

import asyncio
import logging
from logging import getLogger

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from langchain.text_splitter import CharacterTextSplitter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, Project, TTSWorkerResult
from bookcast.services.file import TTSFileService

logger = getLogger(__name__)


class TextToSpeechService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.semaphore = asyncio.Semaphore(3)

    @staticmethod
    def split_script(source_script: str) -> list[str]:
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            separator="\n",
            chunk_size=4000,  # 長過ぎると途中で途切れる
            chunk_overlap=0,
        )
        chunks = text_splitter.split_text(source_script)
        return chunks

    async def _invoke(self, script: str) -> bytes:
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=script,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Speaker1",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Alnilam",
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Speaker2",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Autonoe",
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        return data

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ServerError,)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _generate(self, project: Project, script: str, chapter: Chapter, index: int) -> TTSWorkerResult:
        async with self.semaphore:
            logger.info(f"Generating audio for chapter: {str(chapter)}, index: {index}")
            data = await self._invoke(script)

        logger.info(f"Saving audio for chapter {chapter.chapter_number}, index {index}.")
        source_file_path = TTSFileService.write(project.filename, chapter.chapter_number, index, data)
        TTSFileService.upload_gcs_from_file(source_file_path)
        return TTSWorkerResult(chapter_id=chapter.id, index=index)

    async def _generate_audio(self, project: Project, chapters: list[Chapter]) -> list[TTSWorkerResult]:
        tasks = []
        for chapter in chapters:
            chunked_scripts = self.split_script(chapter.script)
            logger.info(f"Splitting script for chapter {chapter.chapter_number} into {len(chunked_scripts)} chunks.")

            for i, script in enumerate(chunked_scripts):
                tasks.append(self._generate(project, script, chapter, i))

        results = await asyncio.gather(*tasks)
        return results

    async def generate_audio(self, project: Project, chapters: list[Chapter]) -> list[TTSWorkerResult]:
        logger.info("Starting audio generation for chapters.")
        results = await self._generate_audio(project, chapters)
        logger.info("Audio generation completed successfully.")

        return results

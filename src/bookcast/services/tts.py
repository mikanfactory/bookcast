import asyncio
from google import genai
from google.genai import types
import wave

from langchain.text_splitter import CharacterTextSplitter

from bookcast.path_resolver import resolve_audio_path, build_audio_directory
from bookcast.services.script_writing import Chapter


def save_wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


class TextToSpeechService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def split_script(source_script: str) -> list[str]:
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            separator="\n",
            chunk_size=8000,
            chunk_overlap=0,
        )
        chunks = text_splitter.split_text(source_script)
        return chunks

    async def _generate(self, semaphore, script: str, chapter: Chapter, index: int):
        async with semaphore:
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
        print(f"Save audio. index: {index}")
        print(f"candidate: {len(response.candidates)}")
        print(f"parts: {len(response.candidates[0].content.parts)}")

        audio_dir = build_audio_directory(chapter.filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        filename = resolve_audio_path(chapter.filename, chapter.chapter_number, index)
        save_wave_file(str(filename), data)
        return filename

    async def _generate_audio(self, source_script: str, chapter: Chapter):
        semaphore = asyncio.Semaphore(5)
        chunked_scripts = self.split_script(source_script)
        print(f"Total chunks to process: {len(chunked_scripts)}")
        tasks = []
        for i, script in enumerate(chunked_scripts):
            tasks.append(self._generate(semaphore, script, chapter, i))

        results = await asyncio.gather(*tasks)
        return results

    def generate_audio(self, source_script: str, chapter: Chapter):
        return asyncio.run(self._generate_audio(source_script, chapter))

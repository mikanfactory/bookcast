import os
import wave
import pathlib

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    sample_dir = pathlib.Path("downloads/opening_sample")
    sample_dir.mkdir(parents=True, exist_ok=True)

    filename = str(sample_dir / filename)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def generate_tts(voice_name: str):
    contents = """つんどく消化チャンネル、Bookcast"""
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        ),
    )

    data = response.candidates[0].content.parts[0].inline_data.data

    file_name = f"{voice_name}.wav"
    wave_file(file_name, data)  # Saves the file to current directory


client = genai.Client(api_key=GEMINI_API_KEY)
voice_names = [
    "Alnilam",
    # "Autonoe",
    # "Zephyr",
    # "Puck",
    # "Charon",
    # "Kore",
    # "Fenrir",
    # "Leda",
    # "Orus",
    # "Aoede",
    # "Callirrhoe",
    # "Autonoe",
    # "Enceladus",
    # "Iapetus",
    # "Umbriel",
    # "Algieba",
    # "Despina",
    # "Erinome",
    # "Algenib",
    # "Rasalgethi",
    # "Laomedeia",
    # "Achernar",
    # "Alnilam",
    # "Schedar",
    # "Gacrux",
    # "Pulcherrima",
    # "Achird",
    # "Zubenelgenubi",
    # "Vindemiatrix",
    # "Sadachbia",
    # "Sadaltager",
    # "Sulafat",
]

for voice_name in voice_names:
    print(f"Generating TTS for voice: {voice_name}")
    generate_tts(voice_name)

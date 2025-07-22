from bookcast.services.tts import TextToSpeechService
from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import resolve_script_path


def main():
    filename = "chapter3.pdf"
    script_path = resolve_script_path(filename, 1)
    with open(script_path, "r") as f:
        script_text = f.read()

    service = TextToSpeechService(api_key=GEMINI_API_KEY)
    service.generate_audio(script_text)

    # result = service.split_script(script_text)
    # for r in result:
    #     print("*************************************************")
    #     print(r)


if __name__ == "__main__":
    main()

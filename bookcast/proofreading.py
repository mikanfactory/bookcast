from config import *
from google import genai
from google.genai import types

from transformers import AutoTokenizer

PROOFREADING_MODEL = "gemini-2.0-flash-lite-001"
tokenizer = AutoTokenizer.from_pretrained("google/gemma-7b-it")


def generate_content_from_string(
    text: str, prompt: str, model: str = PROOFREADING_MODEL
) -> str:
    """
    Generate content from a text using Google Gemini AI.

    Args:
        text: Summary text to send to the AI model
        prompt: Prompt to send to the AI model
        model: AI model to use (defaults to SUMMARY_MODEL)

    Returns:
        Generated text content
    """
    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(system_instruction=prompt),
        contents=text,
    )

    return response.text


def proofread_text1(text: str) -> str:
    """
    校正を行う。この部分ではPDFからのテキストを受け取り、改行やスペースの調整を行う。

    Args:
        text: Path to the PDF file

    Returns:
        Generated narration text
    """
    prompt = """次の文章は画像化してOCRをかけたものです。この文章を校正してください。

- ところどころ単語間にスペースや改行が挿入されているため、このスペースや改行を削除してください。
- 1文の中で改行が含まれている場合も、改行を取り除いてください。
- それ以外の文章は全く変更しないでください。
"""

    return generate_content_from_string(text, prompt)


def proofread_text2(text: str) -> str:
    """
    校正を行う。この部分では意味をなしていない文章を取り除く。

    Args:
        text: Path to the PDF file

    Returns:
        Generated narration text
    """
    prompt = """次の文章は画像化してOCRをかけたものです。この文章をもとに校正した文章をオーディオブックとして再生しようとしています。
そこで
- 文章の間で、意味を成していない文字が含まれている場合は、それを取り除いてください。
- 日本語以外のプログラミング言語のコードが含まれている場合は、それを取り除いてください。
- 図や表に含まれる文字を文字起こししており、読み上げても理解できないは、それも取り除いてください。
- それ以外の文章は全く変更しないでください。
"""

    return generate_content_from_string(text, prompt)


def split_by_token_limit(text, limit):
    tokens = tokenizer.tokenize(text)
    chunks = []
    while tokens:
        chunk = tokens[:limit]
        text_chunk = tokenizer.convert_tokens_to_string(chunk)
        chunks.append(text_chunk)
        tokens = tokens[limit:]
    return chunks


def main():
    with open("downloads/プログラマー脳.txt", "r") as f:
        input_text = f.read()

    input_texts = split_by_token_limit(input_text, 7000)
    for i, txt in enumerate(input_texts):
        processed_text = proofread_text1(txt)
        processed_text = proofread_text2(processed_text)
        with open(f"downloads/プログラマー脳_{i}.txt", "w") as f:
            f.write(processed_text)


if __name__ == "__main__":
    main()

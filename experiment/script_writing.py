from bookcast.script_writing import *


async def __generate_script():
    filename = "プログラマー脳.pdf"
    start_page, end_page = 58, 72

    text_dir = build_text_directory(filename)

    base_texts = []
    text = "文章は「プログラマー脳」の第3章です。\n"
    for page_num in range(start_page, end_page + 1):
        text_path = text_dir / f"page_{page_num:03d}.txt"
        with open(text_path, "r", encoding="utf-8") as f:
            text += f.read() + "\n"

    base_texts.append(text)

    podcast_setting = PodcastSetting(
        num_of_people=2,
        personality1_name="ジェームズ",
        personality2_name="アリス",
        length=10,
        prompt=build_prompt(),
    )
    await combine(filename, base_texts, podcast_setting)


def main():
    asyncio.run(__generate_script())


if __name__ == "__main__":
    main()

import os
import sys
import re
import argparse
from pathlib import Path
import logging
from typing import List, Tuple, Optional

import pypdf
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import io
from google import genai
from google.genai import types

from config import GEMINI_API_KEY

OCR_AVAILABLE = True


class PDFChapterSplitter:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path("downloads") / self.pdf_path.stem
        self.reader = None

        # ログ設定
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def extract_text_with_ocr(self, page_image: Image.Image) -> str:
        """
        OCRを使用してページ画像からテキストを抽出

        Args:
            page_image: ページの画像

        Returns:
            抽出されたテキスト
        """
        try:
            # OCRで日本語と英語を対象にテキスト抽出
            text = pytesseract.image_to_string(page_image, lang="jpn")
            return text
        except Exception as e:
            self.logger.warning(f"OCR extraction failed: {e}")
            return ""

    def load_pdf(self) -> bool:
        try:
            self.reader = pypdf.PdfReader(str(self.pdf_path))
            return True
        except Exception as e:
            self.logger.error(f"PDFの読み込みに失敗しました: {e}")
            return False

    def extract_text_from_page(self, page_num: int) -> str:
        try:
            text = self._ocr_page(page_num)

            return text
        except Exception as e:
            self.logger.error(f"ページ {page_num + 1} のテキスト抽出に失敗: {e}")
            return ""

    def _ocr_page(self, page_num: int) -> str:
        try:
            images = convert_from_path(
                self.pdf_path, first_page=page_num + 1, last_page=page_num + 1, dpi=300
            )
            if images:
                text = self._gemini_ocr(images[0])
                return text
        except Exception as e:
            self.logger.error(f"OCR処理に失敗 (ページ {page_num + 1}): {e}")

        return ""

    def _gemini_ocr(self, image: Image.Image) -> str:
        """Gemini APIを使用してOCRを実行"""
        try:
            # 画像をbase64エンコード
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_data = buffer.getvalue()

            # Gemini APIでOCRを実行
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type="image/jpeg",
                    ),
                    "この画像から日本語と英語のテキストを抽出してください。章のタイトルや見出しを特に注意深く読み取ってください。テキストのみを返してください。",
                ],
            )

            return response.text
        except Exception as e:
            self.logger.error(f"Gemini OCR処理に失敗: {e}")
            return ""

    def detect_chapters_from_text(self) -> List[int]:
        # OCR結果保存用ディレクトリを作成
        ocr_dir = self.output_dir / "ocr"
        ocr_dir.mkdir(parents=True, exist_ok=True)

        chapter_start_pages = []

        for page_num in range(len(self.reader.pages)):
            self.logger.info(
                f"ページ {page_num + 1}/{len(self.reader.pages)} を処理中..."
            )

            # 1. OCRを実行してテキストを抽出
            text = self._ocr_page(page_num)

            # 2. OCR結果をファイルに保存
            ocr_file_path = ocr_dir / f"page_{page_num + 1:03d}.txt"
            with open(ocr_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.logger.debug(f"OCR結果を保存: {ocr_file_path}")

            # 3. 新しい章の開始ページかどうかを検出
            if self._is_chapter_start_page(page_num, text):
                chapter_start_pages.append(page_num)
                self.logger.info(f"新しい章の開始を検出: ページ {page_num + 1}")

        return chapter_start_pages

    def _is_chapter_start_page(self, page_num: int, text: str) -> bool:
        """Gemini APIを使用して新しい章の開始ページかどうかを判定"""
        try:
            # ページ画像を取得
            images = convert_from_path(
                self.pdf_path, first_page=page_num + 1, last_page=page_num + 1, dpi=300
            )

            if not images:
                return False

            # 画像をバイト形式に変換
            buffer = io.BytesIO()
            images[0].save(buffer, format="PNG")
            image_data = buffer.getvalue()

            # Gemini APIで章開始判定を実行
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = """次の画像は本をスキャンして得られたページです。章ごとに分割するために、章が開始したページを検出する必要があります。
            新しい章が始まったかどうかを検出してください。回答は「はい」または「いいえ」でお答えください。
            """
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type="image/jpeg",
                    ),
                    prompt,
                ],
            )

            # 回答を解析
            answer = response.text.strip().lower()
            is_chapter_start = "はい" in answer or "yes" in answer

            self.logger.debug(
                f"ページ {page_num + 1} 章開始判定: {response.text} -> {is_chapter_start}"
            )
            return is_chapter_start

        except Exception as e:
            self.logger.error(f"章開始判定に失敗 (ページ {page_num + 1}): {e}")
            raise

    def split_chapters(self, chapter_start_pages: List[int]) -> List[str]:
        if not chapter_start_pages:
            self.logger.warning("章が検出されませんでした。")
            return []

        # PDFディレクトリを作成
        pdf_dir = self.output_dir / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        for i, start_page in enumerate(chapter_start_pages):
            # 次の章の開始ページを取得（最後の章の場合は最終ページ）
            end_page = (
                chapter_start_pages[i + 1] - 1
                if i + 1 < len(chapter_start_pages)
                else len(self.reader.pages) - 1
            )

            output_path = pdf_dir / f"chapter{i + 1}.pdf"

            try:
                self._create_chapter_pdf(start_page, end_page, output_path)
                created_files.append(str(output_path))
                self.logger.info(
                    f"章 {i + 1}: ページ {start_page + 1}-{end_page + 1} → {output_path}"
                )
            except Exception as e:
                self.logger.error(f"章 {i + 1} の分割に失敗: {e}")
                raise

        return created_files

    def _create_chapter_pdf(
        self, start_page: int, end_page: int, output_path: Path
    ) -> None:
        writer = pypdf.PdfWriter()

        for page_num in range(start_page, end_page + 1):
            if page_num < len(self.reader.pages):
                writer.add_page(self.reader.pages[page_num])

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

    def process(self) -> List[str]:
        self.logger.info(f"PDFファイルを処理中: {self.pdf_path}")

        if not self.load_pdf():
            return []

        self.logger.info(f"総ページ数: {len(self.reader.pages)}")

        # OCRとテキストから章開始ページを検出
        self.logger.info("OCRによる章検出を開始...")
        chapter_start_pages = self.detect_chapters_from_text()
        self.logger.info(f"検出された章開始ページ数: {len(chapter_start_pages)}")

        if chapter_start_pages:
            self.logger.info("\n検出された章開始ページ:")
            for i, page_num in enumerate(chapter_start_pages):
                self.logger.info(f"  章 {i + 1}: ページ {page_num + 1}")

            self.logger.info(f"\n出力ディレクトリ: {self.output_dir}")
            created_files = self.split_chapters(chapter_start_pages)
            self.logger.info("\n分割完了!")
            return created_files
        else:
            self.logger.warning("章を検出できませんでした。")
            return []


def main():
    parser = argparse.ArgumentParser(description="PDFを章ごとに分割するスクリプト")
    parser.add_argument("pdf_file", help="分割するPDFファイル")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログを表示")

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not os.path.exists(args.pdf_file):
        print(f"エラー: ファイルが見つかりません: {args.pdf_file}")
        sys.exit(1)

    try:
        splitter = PDFChapterSplitter(args.pdf_file)
        created_files = splitter.process()

        print(f"\n✅ 処理完了!")
        print(f"📁 出力ディレクトリ: {splitter.output_dir}")
        print(f"📄 作成されたファイル数: {len(created_files)}")
        for file_path in created_files:
            print(f"  - {os.path.basename(file_path)}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

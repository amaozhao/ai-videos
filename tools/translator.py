import os
import time

import srt
from deep_translator import DeeplTranslator, GoogleTranslator
from dotenv import dotenv_values
from openai import OpenAI


class Translator:
    def __init__(self, input_dir, output_dir, service=None):
        config = dotenv_values(".env")
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.client = OpenAI(
            api_key=config.get("API_KEY"),
            base_url=config.get("BASE_URL"),
        )
        # self.gpt_model = "moonshot-v1-8k"
        self.gpt_model = config.get("GPT_MODEL", "gpt-3.5-turbo")
        self.dl_key = config.get("DEEPL_KEY")
        self.service = service or "chatGPT"
        self.chunk_size = 8
        self.delimiter = "||"

    def run(self):
        for root, _, filenames in os.walk(self.input_dir):
            rel_path = os.path.relpath(root, self.input_dir)
            output_path = os.path.join(self.output_dir, rel_path)
            os.makedirs(output_path, exist_ok=True)

            for filename in filenames:
                if filename.endswith(".srt"):
                    self.translate_file(root, output_path, filename)
                    time.sleep(1)

    def replace(self, content):
        content = content.replace("您", "你")
        return content

    def chunk_subs(self, subs):
        chunked_subs = [
            subs[i: i + self.chunk_size] for i in range(0, len(subs), self.chunk_size)
        ]
        return chunked_subs

    def translate_file(self, dirpath, output_path, filename):
        input_file = os.path.join(dirpath, filename)
        output_file = os.path.join(output_path, filename)

        with open(input_file, "r", encoding="utf-8") as f:
            subs = list(srt.parse(f.read()))
        print(f"start translate: {input_file}")

        chunk_subs = self.chunk_subs(subs)

        output_subs = []

        for ch_idx, chunks in enumerate(chunk_subs):
            joined_chunks = self.delimiter.join([c.content for c in chunks])
            translated_chunks = self.translate_text(joined_chunks)
            translations = translated_chunks.split(self.delimiter)
            if len(chunks) != len(translations):
                for t in chunks:
                    _translated = self.translate_text(t.content)
                    _translated = self.replace(_translated)
                    new_sub = srt.Subtitle(
                        index=t.index,
                        start=t.start,
                        end=t.end,
                        content=_translated + "\n" + t.content,
                    )
                    output_subs.append(new_sub)
            else:
                for idx, t in enumerate(translations):
                    t = self.replace(t)
                    new_sub = srt.Subtitle(
                        index=subs[idx + ch_idx * self.chunk_size].index,
                        start=subs[idx + ch_idx * self.chunk_size].start,
                        end=subs[idx + ch_idx * self.chunk_size].end,
                        content=t + "\n" + subs[idx + ch_idx * self.chunk_size].content,
                    )
                    output_subs.append(new_sub)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(srt.compose(output_subs))

    def translate_text(self, text):
        if self.service == "chatGPT":
            return self.chatgpt_translate(text)
        if self.service == "deepl":
            return DeeplTranslator(
                api_key=self.dl_key, source="en", target="zh", use_free_api=True
            ).translate(text)
        if self.service == "google":
            return GoogleTranslator(
                source="en",
                target="zh-CN",
            ).translate(text)

    def chatgpt_translate(self, text):
        _prompt = """
        你是一位专业的翻译专家,精通英语和中文。现在需要你将指定目录下的所有英文字幕文件翻译成中文字幕文件,注意以下要求:
        1. 仅翻译现有内容,不添加新内容。
        2. 只输出翻译后的中文文本,不输出其他内容。
        3. 遇到专业名词时,保留原文。
        4. 如果源字幕有错误,请予以更正。
        5. 使用简洁语言,避免冗余。
        6. 使用"你"代替"您"。
        7. 直接开始翻译,不要添加任何前言。
        我的原文是:
        """
        prompt = "\n".join(_prompt.split("\n")).replace(" ", "")
        prompt += text
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt},
                ],
                model=self.gpt_model,
            )
            content = response.choices[0].message.content
            translation = content.strip() if content else text.strip()
            time.sleep(20)
        except Exception as e:
            print(f"翻译出错: {e}")
            translation = text
        return translation


if __name__ == "__main__":
    input_dir = "/home/amaozhao/workspace/ai-videos/test"
    output_dir = "/home/amaozhao/workspace/ai-videos/sub-output"

    translator = Translator(input_dir, output_dir, service="google")
    translator.run()

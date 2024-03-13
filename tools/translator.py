import os
import time

from deep_translator import DeeplTranslator
from dotenv import dotenv_values
import srt
from openai import OpenAI

MAX_CHARACTERS = 7000


class Translator:
    def __init__(self, input_dir, output_dir, service=None):
        config = dotenv_values(".env")
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.client = OpenAI(
            api_key=config.get('API_KEY'),
            base_url=config.get('BASE_URL'),
        )
        self.dl_key = config.get('DEEPL_KEY')
        self.service = service or 'chatGPT'

    def translate_subtitles(self):
        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            rel_path = os.path.relpath(dirpath, self.input_dir)
            output_path = os.path.join(self.output_dir, rel_path)
            os.makedirs(output_path, exist_ok=True)

            for filename in filenames:
                if filename.endswith(".srt"):
                    self.translate_file(dirpath, output_path, filename)
                    time.sleep(1)

    def replace(self, content):
        content = content.replace('您', '你')
        return content

    def translate_file(self, dirpath, output_path, filename):
        input_file = os.path.join(dirpath, filename)
        output_file = os.path.join(output_path, filename)

        with open(input_file, "r", encoding="utf-8") as f:
            subs = list(srt.parse(f.read()))

        output_subs = []
        text_to_translate = ""

        for sub in subs:
            new_text = sub.content
            if len(text_to_translate) + len(new_text) + 1 <= MAX_CHARACTERS:
                text_to_translate += "\n" + new_text
            else:
                translation = self.translate_text(text_to_translate)
                translations = translation.split("\n")
                for t in translations:
                    t = self.replace(t)
                    new_sub = srt.Subtitle(
                        index=sub.index, start=sub.start,
                        end=sub.end, content=t
                    )
                    output_subs.append(new_sub)
                text_to_translate = new_text

        if text_to_translate:
            translation = self.translate_text(text_to_translate)
            translations = translation.split("\n")
            for idx, t in enumerate(translations):
                new_sub = srt.Subtitle(
                    index=subs[idx].index,
                    start=subs[idx].start,
                    end=subs[idx].end,
                    content=t + "\n" + subs[idx].content,
                )
                output_subs.append(new_sub)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(srt.compose(output_subs))

    def translate_text(self, text):
        if self.service == 'chatGPT':
            return self.chatgpt_translate(text)
        if self.service == 'deepl':
            return DeeplTranslator(
                api_key=self.dl_key,
                source="en",
                target="zh",
                use_free_api=True
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
        prompt = '\n'.join(_prompt.split('\n')).replace(' ', '')
        prompt += text
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt},
                ],
                model="moonshot-v1-8k",
            )
            content = response.choices[0].message.content
            translation = content.strip() if content else text.strip()
        except Exception as e:
            print(f"翻译出错: {e}")
            translation = text
        return translation


if __name__ == "__main__":
    input_dir = "/home/amaozhao/workspace/ai-videos/test"
    output_dir = "/home/amaozhao/workspace/ai-videos/sub-output"

    translator = Translator(input_dir, output_dir)
    translator.translate_subtitles()

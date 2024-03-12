import os
import time

from dotenv import dotenv_values
import srt
from openai import OpenAI

MAX_CHARACTERS = 7000


class Translator:
    def __init__(self, input_dir, output_dir):
        config = dotenv_values(".env")
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.client = OpenAI(
            api_key=config.get('API_KEY'),
            base_url=config.get('BASE_URL'),
        )
        self.prompt = """
        你是一位专业的翻译专家并精通各种语言。我需要把指定目录下的所有 str 英文字幕文件翻译成中文字幕文件，要求如下：
        1. 不要自行创建新的字幕内容;
        2. 只输出翻译后的中文文本,不要输出其他任何内容;
        3. 如果需要将当前字幕与下一条字幕合并翻译,则在当前行重复输出中文翻译文本;
        4. 如何源字幕中出现专业名词，保留它;
        5. 如果源字幕中有错误，需要你更正它;
        6. 在翻译过程中请尽量使用简洁的语言,避免冗余。
        """

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
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": text},
                ],
                model="moonshot-v1-8k",
            )
            translation = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"翻译出错: {e}")
            translation = text
        return translation


if __name__ == "__main__":
    input_dir = "/home/amaozhao/workspace/ai-videos/test"
    output_dir = "/home/amaozhao/workspace/ai-videos/sub-output"

    translator = Translator(input_dir, output_dir)
    translator.translate_subtitles()

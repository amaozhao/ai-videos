import os
from openai import OpenAI
import srt


# 窗口大小和步长
WINDOW_SIZE = 1000
STEP_SIZE = 300


class SubtitleTranslator:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.max_characters = 1800
        self.separator = "|"
        self.client = OpenAI(
            api_key="sk-JhU8PMFqdpsefj7D49yWqk4J5eADdB9QAihZV06uurPw64BK",
            base_url="https://api.moonshot.cn/v1",
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
    
    def translate_srt_file(self, srt_file):
        translated_srt = ''
        batch = []
        batch_text = ''

        for line in srt_file:
            if line.text.strip():
                if len(batch_text) + len(line.text) + len(self.separator) > self.max_characters:
                    translated_batch = self.translate_batch(batch_text)
                    for batch_line in batch:
                        translated_srt += f"{batch_line.start} --> {batch_line.end}\n{translated_batch}\n\n"
                    batch = []
                    batch_text = line.text
                else:
                    batch.append(line)
                    batch_text += self.separator + line.text

        if batch_text:
            translated_batch = self.translate_batch(batch_text)
            for batch_line in batch:
                translated_srt += f"{batch_line.start} --> {batch_line.end}\n{translated_batch}\n\n"

        return translated_srt

    def translate_batch(self, batch_text):
        batch_parts = batch_text.split(self.separator)
        translated_parts = []
        
        for part in batch_parts:
            part = part.strip()
            if part:
                translated_part = self.translate_text(part)
                translated_parts.append(translated_part)

        return self.separator.join(translated_parts)

    def translate_text(self, text):
        try:
            # response = self.client.chat.completions.create(
            #     messages=[
            #         {"role": "system", "content": self.prompt},
            #         {"role": "user", "content": window_text}
            #     ],
            #     model="moonshot-v1-8k",
            # )
            # translation = response.choices[0].message.content.strip()
            translation = '''
    在我们深入整个材料之前，我想向您展示如何有效地操作这个课程。
    首先，最重要的事实之一是，这个课程已经调整为以1.25甚至1.5的速度播放，好吗？
    要启用此选项，您需要去那里，点击这里，只需考虑选择1.25或甚至1.5的速度。
    在我们的课程窗口下方，我们有不同的标签。
    第一个是概览，在这里您可以找到有关整个课程的信息，好吗，所以如果我去这里并点击显示更多，那里就有描述、特点、关于我和我的一切都在那里，好吗？
    接下来我们有一个叫做问答的空间，您可以在那里提问或搜索已经解释过的主题的答案。
    我会尽快在那里回复，但最多可能需要48小时，好吗？
    然后我们有笔记，您可以在讲座的特定部分留下笔记，好吗？
            '''
            return translation
        except Exception as e:
            print(f"翻译出错: {e}")
            translation = text
            return translation

    def translate_subtitles(self):
        # 遍历输入目录及其子目录
        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            # 创建对应的输出目录
            rel_path = os.path.relpath(dirpath, self.input_dir)
            output_path = os.path.join(self.output_dir, rel_path)
            os.makedirs(output_path, exist_ok=True)

            # 处理目录中的所有 .srt 文件
            for filename in filenames:
                if filename.endswith(".srt"):
                    self.translate_file(dirpath, output_path, filename)

    def translate_file(self, dirpath, output_path, filename):
        input_file = os.path.join(dirpath, filename)
        output_file = os.path.join(output_path, filename)

        # 解析输入字幕文件
        with open(input_file, "r", encoding="utf-8") as f:
            subs = list(srt.parse(f.read()))

        # 创建输出字幕列表
        output_subs = []

        window_start = 0
        while window_start < len(subs):
            window_end = window_start + 1
            window_text = subs[window_start].content

            # 构建当前窗口的字幕文本
            while window_end < len(subs):
                next_sub_text = subs[window_end].content
                if len(window_text) + len(next_sub_text) + 1 > WINDOW_SIZE:
                    break
                window_text += "\n" + next_sub_text
                window_end += 1

            # 翻译当前窗口的字幕
            try:
                # response = self.client.chat.completions.create(
                #     messages=[
                #         {"role": "system", "content": self.prompt},
                #         {"role": "user", "content": window_text}
                #     ],
                #     model="moonshot-v1-8k",
                # )
                # translation = response.choices[0].message.content.strip()
                translation = '''
在我们深入整个材料之前，我想向您展示如何有效地操作这个课程。
首先，最重要的事实之一是，这个课程已经调整为以1.25甚至1.5的速度播放，好吗？
要启用此选项，您需要去那里，点击这里，只需考虑选择1.25或甚至1.5的速度。
在我们的课程窗口下方，我们有不同的标签。
第一个是概览，在这里您可以找到有关整个课程的信息，好吗，所以如果我去这里并点击显示更多，那里就有描述、特点、关于我和我的一切都在那里，好吗？
接下来我们有一个叫做问答的空间，您可以在那里提问或搜索已经解释过的主题的答案。
我会尽快在那里回复，但最多可能需要48小时，好吗？
然后我们有笔记，您可以在讲座的特定部分留下笔记，好吗？
                '''
            except Exception as e:
                print(f"翻译出错: {e}")
                translation = window_text

            # 将翻译结果拆分为原始字幕顺序
            translations = translation.split("\n")
            for i in range(window_start, window_end):
                print(window_start, window_end)
                sub = subs[i]
                new_sub = srt.Subtitle(
                    index=sub.index,
                    start=sub.start,
                    end=sub.end,
                    proprietary=sub.proprietary,
                    content=translations[i - window_start],
                )
                output_subs.append(new_sub)

            # 移动窗口
            window_start = window_end - STEP_SIZE

        # 保存输出字幕文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(srt.compose(output_subs))


if __name__ == "__main__":
    # 使用示例
    input_dir = "/home/amaozhao/workspace/ai-videos/test"
    output_dir = "/home/amaozhao/workspace/ai-videos/sub-output"

    translator = SubtitleTranslator(input_dir, output_dir)
    translator.translate_subtitles()

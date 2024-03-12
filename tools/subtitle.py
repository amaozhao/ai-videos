import os
import re

import spacy
import srt


class SubtitleProcessor:
    def __init__(self):
        # 初始化句子检测器
        self.nlp = spacy.load("en_core_web_sm")

    def remove_filler_words(self, text):
        filler_words = ["um", "uh", "er", "ah", "like", "okay", "right", "you know"]
        pattern = r"\b(" + r"|".join(filler_words) + r")\b"
        return re.sub(pattern, "", text, flags=re.IGNORECASE)

    def fix_common_errors(self, text):
        corrections = {
            "teh": "the",
            "doesnt": "doesn't",
            "cant": "can't",
            "mid journey": "midjourney",
            "mid-journey": "midjourney",
            "MeetJourney": "midjourney",
            "meetjourney": "midjourney",
            "Meetjourney": "midjourney",
            "meetJourney": "midjourney",
            "chat gbt": "chatGPT",
            "chatgbt": "chatGPT",
            # 添加更多的纠正
        }
        for mistake, correction in corrections.items():
            text = re.sub(
                r"\b" + mistake + r"\b", correction, text, flags=re.IGNORECASE
            )
        return text

    def is_complete_sentence(self, text):
        doc = self.nlp(text)
        sentences = list(doc.sents)
        if len(sentences) == 1 and sentences[0].text.strip() == text.strip():
            return True
        return False

    def merge_lines(self, subtitle):
        lines = subtitle.content.split("\n")
        merged = []
        current_line = ""
        for line in lines:
            line = line.strip()
            if line:
                if self.is_complete_sentence(current_line + " " + line):
                    if current_line:
                        merged.append(current_line.strip())
                    current_line = line
                else:
                    current_line += " " + line
        if current_line:
            merged.append(current_line.strip())

        # 创建一个新的字幕条目,保留原始时间戳
        new_subtitle = srt.Subtitle(
            index=subtitle.index,
            start=subtitle.start,
            end=subtitle.end,
            content=" ".join(merged),
        )
        return new_subtitle

    def process_srt_files(self, input_dir, output_dir):
        # 创建输出根目录(如果不存在)
        os.makedirs(output_dir, exist_ok=True)

        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith(".srt"):
                    input_path = os.path.join(root, file)
                    subs = srt.parse(open(input_path, encoding="utf-8").read())

                    processed_subs = []
                    for sub in subs:
                        new_sub = self.merge_lines(sub)
                        new_sub.content = self.fix_common_errors(new_sub.content)
                        new_sub.content = self.remove_filler_words(new_sub.content)
                        processed_subs.append(new_sub)

                    # 构建输出文件路径,保持与输入目录结构一致
                    relative_path = os.path.relpath(input_path, input_dir)
                    output_path = os.path.join(output_dir, relative_path)
                    output_dir_path = os.path.dirname(output_path)
                    os.makedirs(output_dir_path, exist_ok=True)

                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(srt.compose(processed_subs))


if __name__ == "__main__":
    # 使用示例
    processor = SubtitleProcessor()
    input_dir = "/home/amaozhao/Downloads/\
        AI Art Midjourney Passive Income Make and Sell Arts (2024)"
    output_dir = "/home/amaozhao/Downloads/tt"
    processor.process_srt_files(input_dir, output_dir)

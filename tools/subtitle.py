import os
import re

import srt


class SubtitleProcessor:

    def remove_filler_words(self, text):
        filler_words = ["um", "uh", "er", "ah"]
        pattern = r"\b(" + r"|".join(filler_words) + r")\b"
        return re.sub(pattern, "", text, flags=re.IGNORECASE)

    def fix_common_errors(self, text):
        corrections = {
            "DID": "D-ID",
            "Kyber": "Kaiber",
            "Kyber AI": "Kaiber AI",
            "MeetJourney": "MidJourney",
            "Meetjourney": "MidJourney",
            "cant": "can't",
            " chad ": " chat ",
            "chat DPT": "chatGPT",
            "chat GPD": "chatGPT",
            "chat LGBT": "chatGPT",
            "chat dbt": "chatGPT",
            "chat dvd": "chatGPT",
            "chat gbd": "chatGPT",
            "chat gbt": "chatGPT",
            "chat gpt": "chatGPT",
            "chat jpg": "chatGPT",
            "chat jpt": "chatGPT",
            "chatDPG": "chatGPT",
            "chatDPT": "chatGPT",
            "chatgbt": "chatGPT",
            "doesnt": "doesn't",
            "meetJourney": "MidJourney",
            "meetjourney": "MidJourney",
            "mid journey": "MidJourney",
            "mid-journey": "MidJourney",
            "midjourney": "MidJourney",
            "teh": "the",
            # 添加更多的纠正
        }
        for mistake, correction in corrections.items():
            text = re.sub(
                r"\b" + mistake + r"\b", correction, text, flags=re.IGNORECASE
            )
        return text

    def is_complete_sentence(self, text):
        text = text.strip()
        if text.endswith(('.', ';', '?')):
            return True
        return False

    def merge_subtitles(self, subtitles):
        sub_list = []
        processed_subs = []
        result_sub = []
        for sub in subtitles:
            if sub.content in ('.', ',', '?'):
                continue
            if sub_list:
                sub_list.append(sub)
                check_sentence = ' '.join([s.content for s in sub_list])
                if self.is_complete_sentence(check_sentence):
                    processed_subs.append(sub_list)
                    sub_list = []
            else:
                if self.is_complete_sentence(sub.content):
                    processed_subs.append([sub])
                else:
                    sub_list.append(sub)

        for idx, s_l in enumerate(processed_subs):
            text = ' '.join([_.content for _ in s_l])
            text = self.fix_common_errors(text)
            text = self.remove_filler_words(text)
            new_sub = srt.Subtitle(
                index=idx + 1,
                start=s_l[0].start,
                end=s_l[-1].end,
                content=text
            )
            result_sub.append(new_sub)
        return result_sub

    def process_srt_files(self, input_dir, output_dir):
        # 创建输出根目录(如果不存在)
        os.makedirs(output_dir, exist_ok=True)

        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith(".srt"):
                    input_path = os.path.join(root, file)
                    subs = srt.parse(open(input_path, encoding="utf-8").read())
                    processed_subs = self.merge_subtitles(subs)

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
    input_dir = "/home/amaozhao/Downloads/videos"
    output_dir = "/Users/amaozhao/workspace/ai-videos/output/"
    processor.process_srt_files(input_dir, output_dir)

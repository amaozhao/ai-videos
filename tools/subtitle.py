import os
import re
import srt
import spacy


class SubtitleProcessor:
    def __init__(self):
        # 初始化句子检测器
        self.nlp = spacy.load("en_core_web_sm")

    def remove_filler_words(self, text):
        filler_words = [
            'um', 'uh', 'er', 'ah', 'like',
            'okay', 'right', 'you know'
        ]
        pattern = r'\b(' + r'|'.join(filler_words) + r')\b'
        return re.sub(pattern, '', text, flags=re.IGNORECASE)

    def fix_common_errors(self, text):
        corrections = {
            "teh": "the",
            "doesnt": "doesn't",
            "cant": "can't",
            # 添加更多的纠正
        }
        for mistake, correction in corrections.items():
            text = re.sub(
                r'\b' + mistake + r'\b',
                correction,
                text,
                flags=re.IGNORECASE
            )
        return text

    def is_complete_sentence(self, text):
        doc = self.nlp(text)
        sentences = list(doc.sents)
        if len(sentences) == 1 and sentences[0].text.strip() == text.strip():
            return True
        return False

    def merge_lines(self, subtitle):
        lines = subtitle.content.split('\n')
        merged = []
        current_line = ''
        for line in lines:
            line = line.strip()
            if line:
                if self.is_complete_sentence(current_line + ' ' + line):
                    if current_line:
                        merged.append(current_line.strip())
                    current_line = line
                else:
                    current_line += ' ' + line
        if current_line:
            merged.append(current_line.strip())

        # 创建一个新的字幕条目,保留原始时间戳
        new_subtitle = srt.Subtitle(
            index=subtitle.index,
            start=subtitle.start,
            end=subtitle.end,
            content='\n'.join(merged)
        )
        return new_subtitle

    def get_output_path(self, input_path, output_dir):
        """
        根据输入文件路径和输出目录构建输出文件路径
        """
        input_dir = os.path.dirname(input_path)
        relative_path = os.path.relpath(input_path, input_dir)
        output_path = os.path.join(output_dir, relative_path)
        return output_path

    def process_srt_files(self, input_dir, output_dir):
        # 创建输出目录(如果不存在)
        os.makedirs(output_dir, exist_ok=True)

        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.srt'):
                    input_path = os.path.join(root, file)
                    subs = srt.parse(open(input_path, encoding='utf-8').read())

                    processed_subs = []
                    for sub in subs:
                        new_sub = self.merge_lines(sub)
                        new_sub.content = self.fix_common_errors(
                            new_sub.content
                        )
                        new_sub.content = self.remove_filler_words(
                            new_sub.content
                        )
                        processed_subs.append(new_sub)

                    # 构建输出文件路径
                    output_path = self.get_output_path(input_path, output_dir)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(srt.compose(processed_subs))


if __name__ == "__main__":
    # 使用示例
    processor = SubtitleProcessor()
    input_dir = '/path/to/input/subtitles/directory'
    output_dir = '/path/to/output/directory'
    processor.process_srt_files(input_dir, output_dir)

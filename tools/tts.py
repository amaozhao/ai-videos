import asyncio
import os
from pathlib import Path

import edge_tts
import srt
from pydub import AudioSegment


class TTSConverter:
    def __init__(self):
        self.temp_dir = Path("./tmp")
        # self.voice = "zh-CN-YunxiNeural"
        self.voice = "zh-CN-YunyangNeural"

    def run(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        # 确保输出目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        for dirpath, dirnames, filenames in os.walk(self.input_dir):
            rel_path = os.path.relpath(dirpath, self.input_dir)
            output_path = os.path.join(self.output_dir, rel_path)
            os.makedirs(output_path, exist_ok=True)

            for filename in filenames:
                if filename.endswith(".srt"):
                    self.convert_srt(dirpath, output_path, filename)

        # 清理临时文件
        for temp_file in self.temp_dir.glob("*.mp3"):
            temp_file.unlink()

    def convert_srt(self, dirpath, output_path, filename):
        input_file = os.path.join(dirpath, filename)
        output_filename = os.path.splitext(filename)[0] + ".mp3"
        output_file = os.path.join(output_path, output_filename)

        with open(input_file, "r", encoding="utf-8") as f:
            subs = list(srt.parse(f.read()))

        for idx, sub in enumerate(subs):
            asyncio.run(self.convert_sub(idx, sub))

        self.contact_mp3(subs, output_file)

    async def convert_sub(self, idx, subtitle):
        content = subtitle.content
        if len(content.split('\n')) > 1:
            content = content.split('\n')[0]
        communicate = edge_tts.Communicate(content, self.voice)
        output_file = os.path.join(self.temp_dir, f"{idx}.mp3")
        await communicate.save(output_file)

    def contact_mp3(self, subs, output_file):
        mp3_files = []
        for dirpath, _, filenames in os.walk(self.temp_dir):
            rel_path = os.path.relpath(dirpath, self.input_dir)
            for filename in filenames:
                if filename.endswith(".mp3"):
                    print(dirpath, rel_path)
                    mp3_files.append(os.path.join(dirpath, filename))
        mp3_files.sort()
        audios = []
        for mp3 in mp3_files:
            audios.append(AudioSegment.from_mp3(mp3))

        sub_audio = AudioSegment.silent(duration=0)

        for i, audio in enumerate(audios):
            # 对应的字幕
            sub = subs[i]
            # 获取原始音频的长度(以毫秒为单位)
            audio_length = len(audio)
            sub_start = sub.start
            sub_end = sub.end
            # 字幕时间长度(以毫秒为单位)
            sub_length = int((sub_end - sub_start).total_seconds() * 1000)

            # 判断是否需要压缩
            if sub_length < audio_length:
                audio = self.compress_audio(sub_length, audio_length, audio)
            if i == 0:
                _silence = int(sub_start.total_seconds()) * 1000
                sub_audio += self.create_silence(_silence)
            else:
                previous_sub = subs[i - 1]
                previous_end = previous_sub.end
                _silence = int((sub.start - previous_end).total_seconds() * 1000)
                sub_audio += self.create_silence(_silence)
                sub_audio += audio
        sub_audio.export(output_file, format="mp3")

    def compress_audio(self, sub_length, audio_length, audio):
        if sub_length < audio_length:
            # 计算新的播放速率
            new_rate = audio_length / sub_length

            # 通过调整播放速率来压缩音频
            audio = audio._spawn(
                audio.raw_data,
                overrides={"frame_rate": int(audio.frame_rate * new_rate)},
            )
        return audio

    def create_silence(self, duration):
        silence = AudioSegment.silent(duration=duration)
        return silence


if __name__ == "__main__":
    input_dir = "/home/amaozhao/workspace/ai-videos/sub-output"
    output_dir = "/home/amaozhao/workspace/ai-videos/mp3-output"

    tts = TTSConverter(input_dir, output_dir)
    tts.convert_path()

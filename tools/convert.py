from TTS.utils.synthesizer import Synthesizer
from TTS.tts.models import Tacotron2
import os
import glob
# from pydub import AudioSegment
from moviepy.editor import AudioFileClip


class TTSConverter:
    def __init__(self, tts_model_path, tts_config_path):
        # 初始化Coqui TTS模型
        self.tts_model = Tacotron2(config=tts_config_path, ap=ap)
        self.synthesizer = Synthesizer(
            self.tts_model.ap,
            self.tts_model.net_g,
            self.tts_model.vocoder
        )
        self.synthesizer.load_model(tts_model_path)

    def srt_to_audio(self, srt_file_path, output_dir):
        # 从srt文件中提取文本
        with open(srt_file_path, 'r') as f:
            text = ' '.join([line.strip() for line in f if line.strip()])

        # 使用Coqui TTS合成语音
        wav = self.synthesizer.tts(text)

        # 将wav转换为mp3
        mp3_file_path = os.path.join(
            output_dir,
            os.path.splitext(
                os.path.basename(srt_file_path)
            )[0] + '.mp3'
        )
        # AudioSegment.from_wav(wav).export(mp3_file_path, format='mp3')
        audio = AudioFileClip(wav)
        audio.write_audiofile(mp3_file_path)
        audio.close()

    def convert_dir(self, input_dir, output_dir):
        # 遍历目录下的所有srt文件
        for srt_file in glob.glob(
                os.path.join(input_dir, '**/*.srt'), recursive=True):
            # 获取srt文件的相对路径
            rel_path = os.path.relpath(srt_file, input_dir)
            # 构造输出目录
            out_dir = os.path.join(output_dir, os.path.dirname(rel_path))
            os.makedirs(out_dir, exist_ok=True)
            # 转换srt为mp3
            self.srt_to_audio(srt_file, out_dir)

import asyncio

import edge_tts

TEXT = "欢迎回来。在本课程中，你将踏上激动人心的学习之旅，探索 chatGPT 的世界。"
# VOICE = "zh-CN-YunxiNeural"
VOICE = "zh-CN-YunyangNeural"
OUTPUT_FILE = "test.mp3"


class TTSConvert:
    def __init__(self):
        self.voice = "zh-CN-YunyangNeural"

    async def convert(self, subtitle):
        communicate = edge_tts.Communicate(subtitle.content, self.voice)
        await communicate.save(OUTPUT_FILE)

    def merge_audios(self, audios):
        pass


async def main() -> None:
    """Main function"""
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())

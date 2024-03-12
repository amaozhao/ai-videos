import typer
from tools import SubtitleProcessor, Translator, TTSconvert


app = typer.Typer()


@app.command()
def reset_path(
        input_dir: str,
        output_dir: str = '/home/amaozhao/Downloads/tt'):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, output_dir)


@app.command()
def translate_path(
        input_dir: str,
        output_dir: str = '/home/amaozhao/Downloads/transltion'):
    translator = Translator(input_dir, output_dir)
    translator.translate_subtitles()


@app.command()
def tts_path(
        input_dir: str,
        output_dir: str = '/home/amaozhao/Downloads/tts'):
    tts = TTSconvert(input_dir, output_dir)
    tts.convert_path()


if __name__ == "__main__":
    app()

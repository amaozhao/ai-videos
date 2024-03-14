import typer
from tools import SubtitleProcessor, Transcribe, Translator, TTSconvert


app = typer.Typer()


@app.command()
def reset_path(
        input_dir: str,
        output_dir: str = '~/Downloads/tt'):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, output_dir)


@app.command()
def translate_path(
        input_dir: str,
        output_dir: str = '~/Downloads/transltion',
        service: str = 'deepl'
):
    translator = Translator(input_dir, output_dir, service=service)
    translator.translate_subtitles()


@app.command()
def tts_path(
        input_dir: str,
        output_dir: str = '~/Downloads/tts'):
    tts = TTSconvert(input_dir, output_dir)
    tts.convert_path()


@app.command()
def transcribe_path(
        audio: str,
        model: str = 'medium'):
    transcribe = Transcribe(audio=audio, model=model)
    transcribe.run()


if __name__ == "__main__":
    app()

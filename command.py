from typing import Optional
import typer
from typing_extensions import Annotated
from tools import SubtitleProcessor, Translator, TTSconvert


app = typer.Typer()


@app.command()
def reset_path(
        input_dir: Annotated[str, typer.Argument()],
        output_dir: Annotated[Optional[str], typer.Argument()] = '/home/amaozhao/Downloads/tt'):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, output_dir)


@app.command()
def translate_path(
        input_dir: Annotated[str, typer.Argument()],
        output_dir: Annotated[Optional[str], typer.Argument()] = '/home/amaozhao/Downloads/translation',
        service: str = 'google'
):
    translator = Translator(input_dir, output_dir, service=service)
    translator.translate_subtitles()


@app.command()
def chain_translate(
        input_dir: Annotated[str, typer.Argument()],
        temp_dir: Annotated[Optional[str], typer.Argument()] = '/home/amaozhao/Downloads/tt',
        output_dir: Annotated[Optional[str], typer.Argument()] = '/home/amaozhao/Downloads/translation',
        service: Annotated[str, typer.Argument()] = 'google'
):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, temp_dir)
    translator = Translator(temp_dir, output_dir, service=service)
    translator.translate_subtitles()


@app.command()
def tts_path(
        input_dir: Annotated[str, typer.Argument()],
        output_dir: Annotated[Optional[str], typer.Argument()] = '/home/amaozhao/Downloads/tts'):
    tts = TTSconvert(input_dir, output_dir)
    tts.convert_path()


@app.command()
def transcribe_path(
        audio: Annotated[str, typer.Argument()],
        model: Annotated[Optional[str], typer.Argument()] = 'medium'):
    from tools import Transcribe
    transcribe = Transcribe(audio=audio, model=model)
    transcribe.run()


if __name__ == "__main__":
    app()

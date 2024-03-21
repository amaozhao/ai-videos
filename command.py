from typing import Optional
import typer
from typing_extensions import Annotated
from tools import SubtitleProcessor, Translator, TTSconvert


app = typer.Typer()


@app.command("reset-subtitle")
def reset_path(
        input_dir: Annotated[
            str,
            typer.Argument(help="The directory for reset input path")
        ],
        output_dir: Annotated[
            Optional[str],
            typer.Argument(
                help="The directory for reset path"
            )
        ] = '/home/amaozhao/Downloads/tt'
):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, output_dir)


@app.command("translate-subtitle")
def translate_path(
        input_dir: Annotated[str, typer.Argument(help="The directory for translate input path")],
        output_dir: Annotated[
            Optional[str],
            typer.Argument(
                help="The directory for translate path"
            )
        ] = '/home/amaozhao/Downloads/translation',
        service: str = 'google'
):
    translator = Translator(input_dir, output_dir, service=service)
    translator.translate_subtitles()


@app.command("reset-and-translate")
def chain_translate(
        input_dir: Annotated[
            str,
            typer.Argument(
                help="The directory for reset and translate input path"
            )
        ],
        temp_dir: Annotated[
            Optional[str],
            typer.Argument(
                help="The directory for temp path"
            )
        ] = '/home/amaozhao/Downloads/tt',
        output_dir: Annotated[
            Optional[str],
            typer.Argument(
                help="The directory for output path"
            )
        ] = '/home/amaozhao/Downloads/translation',
        service: Annotated[str, typer.Argument()] = 'google'
):
    processor = SubtitleProcessor()
    processor.process_srt_files(input_dir, temp_dir)
    translator = Translator(temp_dir, output_dir, service=service)
    translator.translate_subtitles()


@app.command("tts")
def tts_path(
        input_dir: Annotated[str, typer.Argument(help="The directory for tts input path")],
        output_dir: Annotated[
            Optional[str],
            typer.Argument(
                help="The directory for output path"
            )
        ] = '/home/amaozhao/Downloads/tts'
):
    tts = TTSconvert(input_dir, output_dir)
    tts.convert_path()


@app.command("transcribe")
def transcribe_path(
        input_path: Annotated[str, typer.Argument(help="The directory for transcribe input path")],
        model: Annotated[
            Optional[str],
            typer.Argument(help="The transcribe model type")
        ] = 'medium'
):
    from tools import Transcribe
    transcribe = Transcribe(audio=input_path, model=model)
    transcribe.run()


if __name__ == "__main__":
    app()

import os
import sys

import torch as th
from demucs.api import Separator, save_audio
from demucs.apply import BagOfModels
from demucs.htdemucs import HTDemucs

# from demucs.pretrained import add_model_flags, ModelLoadingError


class VideoSeparator:
    def __init__(self, input_path, output_path) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.name = "htdemucs"
        self.repo = None
        self.device = "cpu"
        self.shifts = 1
        self.split = True
        self.overlap = 0.25
        self.jobs = 0
        self.segment = None
        self.stem = None
        self.other_method = "add"
        self.int24 = True
        self.float32 = None
        self.clip_mode = "rescale"
        self.flac = None
        self.mp3 = None
        self.mp3_bitrate = 320
        self.mp3_preset = 2
        self.jobs = 0
        self.separator = self.get_separator()

    def get_separator(self):
        return Separator(
            model=self.name,
            repo=self.repo,
            device=self.device,
            shifts=self.shifts,
            split=self.split,
            overlap=self.overlap,
            progress=True,
            jobs=self.jobs,
            segment=self.segment,
        )

    def run(self):
        max_allowed_segment = float("inf")
        if isinstance(self.separator.model, HTDemucs):
            max_allowed_segment = float(self.separator.model.segment)
        elif isinstance(self.separator.model, BagOfModels):
            max_allowed_segment = self.separator.model.max_allowed_segment
        if self.segment is not None and self.segment > max_allowed_segment:
            print(
                "Cannot use a Transformer model with a longer segment "
                f"than it was trained for. Maximum segment is: {max_allowed_segment}"
            )
            return

        if isinstance(self.separator.model, BagOfModels):
            print(
                f"Selected model is a bag of {len(self.separator.model.models)} models. "
                "You will see that many progress bars per track."
            )

        if self.stem is not None and self.stem not in self.separator.model.sources:
            print(
                'error: stem "{stem}" is not in selected model. '
                "STEM must be one of {sources}.".format(
                    stem=self.stem, sources=", ".join(self.separator.model.sources)
                )
            )
            return
        out = os.path.join(self.output_path, self.name)
        os.makedirs(out, exist_ok=True)
        # out.mkdir(parents=True, exist_ok=True)
        print(f"Separated input_path will be stored in {out}")
        for track in self.input_path:
            if not track.exists():
                print(
                    f"File {track} does not exist. If the path contains spaces, "
                    'please try again after surrounding the entire path with quotes "".',
                    file=sys.stderr,
                )
                continue
            print(f"Separating track {track}")

            origin, res = self.separator.separate_audio_file(track)

            if self.mp3:
                ext = "mp3"
            elif self.flac:
                ext = "flac"
            else:
                ext = "wav"
            kwargs = {
                "samplerate": self.separator.samplerate,
                "bitrate": self.mp3_bitrate,
                "preset": self.mp3_preset,
                "clip": self.clip_mode,
                "as_float": self.float32,
                "bits_per_sample": 24 if self.int24 else 16,
            }
            if self.stem is None:
                for name, source in res.items():
                    stem = out / self.filename.format(
                        track=track.name.rsplit(".", 1)[0],
                        trackext=track.name.rsplit(".", 1)[-1],
                        stem=name,
                        ext=ext,
                    )
                    stem.parent.mkdir(parents=True, exist_ok=True)
                    save_audio(source, str(stem), **kwargs)
            else:
                stem = out / self.filename.format(
                    track=track.name.rsplit(".", 1)[0],
                    trackext=track.name.rsplit(".", 1)[-1],
                    stem="minus_" + self.stem,
                    ext=ext,
                )
                if self.other_method == "minus":
                    stem.parent.mkdir(parents=True, exist_ok=True)
                    save_audio(origin - res[self.stem], str(stem), **kwargs)
                stem = out / self.filename.format(
                    track=track.name.rsplit(".", 1)[0],
                    trackext=track.name.rsplit(".", 1)[-1],
                    stem=self.stem,
                    ext=ext,
                )
                stem.parent.mkdir(parents=True, exist_ok=True)
                save_audio(res.pop(self.stem), str(stem), **kwargs)
                # Warning : after poping the stem, selected stem is no longer in the dict 'res'
                if self.other_method == "add":
                    other_stem = th.zeros_like(next(iter(res.values())))
                    for i in res.values():
                        other_stem += i
                    stem = out / self.filename.format(
                        track=track.name.rsplit(".", 1)[0],
                        trackext=track.name.rsplit(".", 1)[-1],
                        stem="no_" + self.stem,
                        ext=ext,
                    )
                    stem.parent.mkdir(parents=True, exist_ok=True)
                    save_audio(other_stem, str(stem), **kwargs)

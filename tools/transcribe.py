import gc
import os
import warnings

import numpy as np
import torch

from whisperx.alignment import align, load_align_model
from whisperx.asr import load_model
from whisperx.audio import load_audio
from whisperx.utils import (
    LANGUAGES,
    TO_LANGUAGE_CODE,
    get_writer
)


class Transcribe:

    def __init__(
            self,
            audio,
            model="medium",
            model_dir=None,
            batch_size=8,
            verbose=True,
            task='transcribe',
            language="en",
            output_format='srt',
            compute_type='int8',
            # alignment params
            align_model=None,
            interpolate_method="nearest",
            no_align=None,
            return_char_alignments=None,
            # vad params
            vad_onset=0.500,
            vad_offset=0.363,
            chunk_size=30,
            # diarization params
            diarize=None,
            min_speakers=None,
            max_speakers=None,
            temperature=0,
            best_of=5,
            beam_size=5,
            patience=1.0,
            length_penalty=1.0,
            suppress_tokens="-1",
            suppress_numerals=None,
            initial_prompt=None,
            condition_on_previous_text=False,
            fp16=True,
            temperature_increment_on_fallback=0.2,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            max_line_width=None,
            max_line_count=None,
            highlight_words=False,
            segment_resolution="sentence",
            threads=4,
            hf_token=None,
            print_progress=False):
        self.audio = audio
        self.model = model
        self.model_dir = model_dir
        self.device = "cpu"
        self.device_index = 0
        self.batch_size = batch_size
        self.verbose = verbose
        self.task = task
        self.language = language
        self.output_format = output_format
        self.compute_type = compute_type
        # alignment params
        self.align_model = align_model
        self.interpolate_method = interpolate_method
        self.no_align = no_align
        self.return_char_alignments = return_char_alignments
        # vad params
        self.vad_onset = vad_onset
        self.vad_offset = vad_offset
        self.chunk_size = chunk_size
        # diarization params
        self.diarize = diarize
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        self.temperature = temperature
        self.best_of = best_of
        self.beam_size = beam_size
        self.patience = patience
        self.length_penalty = length_penalty
        self.suppress_tokens = suppress_tokens
        self.suppress_numerals = suppress_numerals
        self.initial_prompt = initial_prompt
        self.condition_on_previous_text = condition_on_previous_text
        self.fp16 = fp16
        self.temperature_increment_on_fallback = \
            temperature_increment_on_fallback
        self.compression_ratio_threshold = compression_ratio_threshold
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.max_line_width = max_line_width
        self.max_line_count = max_line_count
        self.highlight_words = highlight_words
        self.segment_resolution = segment_resolution
        self.threads = threads
        self.hf_token = hf_token
        self.print_progress = print_progress
        # model_flush: bool = args.pop("model_flush")
        if task == "translate":
            # translation cannot be aligned
            self.no_align = True
        if self.language is not None:
            self.language = self.language.lower()
            if self.language not in LANGUAGES:
                if self.language in TO_LANGUAGE_CODE:
                    self.language = TO_LANGUAGE_CODE[self.language]
                else:
                    raise ValueError(f"Unsupported language: {self.language}")

        if self.model.endswith(".en") and self.language != "en":
            if self.language is not None:
                warnings.warn(
                    f"{self.model} is an English-only model but received \
                        '{self.language}'; using English instead."
                )
            self.language = "en"
        # default to loading english if not specified
        self.align_language = self.language

        if (increment := self.temperature_increment_on_fallback) is not None:
            self.temperature = tuple(
                np.arange(self.temperature, 1.0 + 1e-6, increment)
            )
        else:
            self.temperature = [self.temperature]

        self.faster_whisper_threads = 4
        if (threads := self.threads) > 0:
            torch.set_num_threads(self.threads)
            self.faster_whisper_threads = self.threads
        self.transcribe_model = self.get_model()
        self.align_model, self.align_metadata = self.get_align_model()
        # self.writer = get_writer(self.output_format, self.output_dir)

    def get_asr_options(self):
        return {
            "beam_size": self.beam_size,
            "patience": self.patience,
            "length_penalty": self.length_penalty,
            "temperatures": self.temperature,
            "compression_ratio_threshold": self.compression_ratio_threshold,
            "log_prob_threshold": self.logprob_threshold,
            "no_speech_threshold": self.no_speech_threshold,
            "condition_on_previous_text": False,
            "initial_prompt": self.initial_prompt,
            "suppress_tokens": [
                int(x) for x in self.suppress_tokens.split(",")
            ],
            "suppress_numerals": self.suppress_numerals,
        }

    def get_model(self):
        model = load_model(
            self.model,
            device=self.device,
            device_index=self.device_index,
            download_root=self.model_dir,
            compute_type=self.compute_type,
            language=self.language,
            asr_options=self.get_asr_options(),
            vad_options={
                "vad_onset": self.vad_onset,
                "vad_offset": self.vad_offset
            },
            task=self.task,
            threads=self.faster_whisper_threads
        )
        return model

    def get_align_model(self):
        align_model, align_metadata = load_align_model(
            self.align_language,
            self.device,
            model_name=self.align_model
        )
        return align_model, align_metadata

    def transcription(self, file):
        # Part 1: VAD & ASR Loop
        results = []
        audio = load_audio(file)
        # >> VAD & ASR
        print(">>Performing transcription...")
        result = self.transcribe_model.transcribe(
            audio,
            batch_size=self.batch_size,
            chunk_size=self.chunk_size,
            print_progress=self.print_progress
        )
        results.append((result, file))

        # Unload Whisper and VAD
        # del model
        gc.collect()
        torch.cuda.empty_cache()
        return results

    def align(self, results):
        # Part 2: Align Loop
        align_result = []
        if not self.no_align:
            for result, audio_path in results:
                # >> Align
                if len(results) > 1:
                    input_audio = audio_path
                else:
                    # lazily load audio from part 1
                    input_audio = load_audio(audio_path)

                if self.align_model is not None and len(
                        result["segments"]) > 0:
                    if result.get(
                            "language",
                            "en") != self.align_metadata["language"]:
                        # load new language
                        _f_string = (
                            f"New language found ({result['language']})! "
                            f"Previous was "
                            f"({self.align_metadata['language']}), "
                            "loading new alignment model for new language..."
                        )
                        print(_f_string)
                        self.align_model,
                        self.align_metadata = load_align_model(
                            result["language"],
                            self.device
                        )
                    print(">>Performing alignment...")
                    result = align(
                        result["segments"],
                        self.align_model,
                        self.align_metadata,
                        input_audio,
                        self.device,
                        interpolate_method=self.interpolate_method,
                        return_char_alignments=self.return_char_alignments,
                        print_progress=self.print_progress
                    )

                align_result.append((result, audio_path))
                # Unload align model
                gc.collect()
                torch.cuda.empty_cache()
        return align_result

    def save(self, results):
        word_options = ["highlight_words", "max_line_count", "max_line_width"]
        if self.no_align:
            for option in word_options:
                if getattr(self, option):
                    raise Exception(f"--{option} not possible with --no_align")
        if self.max_line_count and not self.max_line_width:
            warnings.warn(
                "--max_line_count has no effect without --max_line_width")
        writer_args = {arg: getattr(self, arg) for arg in word_options}

        # >> Write
        for result, audio_path in results:
            writer = get_writer(
                self.output_format,
                os.path.dirname(audio_path)
            )
            result["language"] = self.align_language
            writer(result, audio_path, writer_args)

    def run(self):
        for root, dirs, files in os.walk(self.audio):
            for audio in files:
                if audio.endswith('.mp4'):
                    results = self.align(
                        self.transcription(os.path.join(root, audio))
                    )
                    print(1111, results)
                    self.save(results)

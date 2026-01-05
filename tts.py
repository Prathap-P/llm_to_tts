from TTS.api import TTS
import sounddevice as sd
import torch
from TTS.tts.configs.xtts_config import XttsConfig
import numpy as np
from scipy.io import wavfile
import os

torch.serialization.add_safe_globals([XttsConfig])


# vits_tts_model = TTS(
#     model_name="tts_models/en/ljspeech/speedy-speech",
#     # vocoder_name="vocoder_models/en/ljspeech/hifigan"
# )

vits_tts_model = TTS(
    model_name="tts_models/en/ljspeech/glow-tts",
    gpu=False
)

def generate_audio_file(text: str, output_file: str):
    print('Content to be converted to audio: ', text, '\n\n\n')
    vits_tts_model.tts_to_file(text=text, file_path=output_file, split_sentences=False)

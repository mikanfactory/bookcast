from pydub import AudioSegment
from pydub.silence import detect_nonsilent, detect_silence


def normalize(audio, target_dBFS=-16.0):
    change_in_dBFS = target_dBFS - audio.dBFS
    return audio.apply_gain(change_in_dBFS)


def trim_silence(audio, silence_thresh=-40, min_silence_len=500):
    nonsilent_ranges = detect_nonsilent(
        audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
    )
    if not nonsilent_ranges:
        return audio
    start_trim = nonsilent_ranges[0][0]
    end_trim = nonsilent_ranges[-1][1]
    return audio[start_trim:end_trim]


def shorten_long_silences(
    audio, max_silence_len=1000, silence_thresh=-40, replace_with=250
):
    silence_ranges = detect_silence(
        audio, min_silence_len=max_silence_len, silence_thresh=silence_thresh
    )
    output = AudioSegment.empty()
    prev_end = 0
    for start, end in silence_ranges:
        output += audio[prev_end:start]
        output += AudioSegment.silent(duration=replace_with)
        prev_end = end
    output += audio[prev_end:]
    return output


class AudioService:
    def __init__(self):
        pass

    def coordinate_audio(self):
        jingle_audio = AudioSegment.from_mp3("resources/jingle.mp3")
        jingle_audio = normalize(jingle_audio)
        jingle_audio = trim_silence(jingle_audio)

        script_audio = AudioSegment.from_wav("script.wav")
        script_audio = normalize(script_audio)
        script_audio = trim_silence(script_audio)

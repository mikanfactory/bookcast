from logging import getLogger
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from bookcast.path_resolver import resolve_audio_path, resolve_audio_output_path
from bookcast.entities import Chapter

logger = getLogger(__name__)


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


def read_script_audio_files(filename, chapter_number):
    acc = []
    for i in range(10):
        path = resolve_audio_path(filename, chapter_number, i)
        try:
            audio = AudioSegment.from_wav(path)
            acc.append(audio)
        except FileNotFoundError:
            pass

    return acc


class AudioService:
    def _coordinate_jingle(self):
        jingle_audio = AudioSegment.from_mp3("resources/jingle.mp3")
        jingle_audio = normalize(jingle_audio)
        jingle_audio = trim_silence(jingle_audio)

        opening_call = AudioSegment.from_wav("resources/opening_call.wav")
        opening_call = normalize(opening_call)
        opening_call = trim_silence(opening_call)

        opening = jingle_audio.overlay(opening_call, position=8000)

        return opening

    def _coordinate_script(self, chapter: Chapter):
        script_audios = read_script_audio_files(chapter.filename, chapter.chapter_number)
        acc = AudioSegment.empty()
        for script_audio in script_audios:
            script_audio = normalize(script_audio)
            script_audio = trim_silence(script_audio)
            acc += script_audio

        return acc

    def _coordinate_bgm(self, script_audio_size: int):
        bgm_audio = AudioSegment.from_mp3("resources/bgm.mp3")
        bgm_looped = (bgm_audio * (script_audio_size // len(bgm_audio) + 1))[:script_audio_size]
        bgm_quiet = bgm_looped - 13
        return bgm_quiet

    def generate_audio(self, chapter: Chapter):
        logger.info(f"Generating audio for chapter: {str(chapter)}")
        jingle_audio = self._coordinate_jingle()
        script_audio = self._coordinate_script(chapter)

        bgm_audio = self._coordinate_bgm(len(script_audio))
        script_with_bgm = script_audio.overlay(bgm_audio)

        output_audio = jingle_audio + script_with_bgm

        output_path = resolve_audio_output_path(chapter.filename, chapter.chapter_number)
        output_audio.export(output_path, format='wav', bitrate="192k")
        logger.info(f"Audio exported to: {output_path}")

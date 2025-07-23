import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment

from bookcast.path_resolver import resolve_audio_path
from bookcast.services.audio import AudioService


def plot_waveform(audio):
    samples = np.array(audio.get_array_of_samples())
    plt.figure(figsize=(12, 3))
    plt.plot(samples)
    plt.title("Waveform")
    plt.show()


def main():
    # path = resolve_audio_path("chapter3", 1, 0)
    # sample_audio = AudioSegment.from_mp3(path)
    #
    # plot_waveform(sample_audio)

    service = AudioService()
    service.coordinate_audio()


if __name__ == "__main__":
    main()

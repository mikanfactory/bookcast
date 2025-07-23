import numpy as np
import matplotlib.pyplot as plt
from bookcast.path_resolver import resolve_audio_path


def plot_waveform(audio):
    samples = np.array(audio.get_array_of_samples())
    plt.figure(figsize=(12, 3))
    plt.plot(samples)
    plt.title("Waveform")
    plt.show()


def main():
    path = resolve_audio_path("chapter3", 1, 1)
    with open(path, "rb") as f:
        sample_audio = f.read()

    plot_waveform(sample_audio)


if __name__ == "__main__":
    main()

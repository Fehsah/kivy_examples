import numpy as np
from audiostream import get_output, AudioSample


class AudioPlayer:
    def __init__(self, channels, rate, chunk_size):
        super().__init__()
        self.rate = rate
        self.chunk_size = chunk_size
        self.stream = get_output(
            channels=channels, rate=rate, buffersize=chunk_size, encoding=16)
        self.sample = AudioSample()
        print("AudioPlayer Chunksize ", self.chunk_size)
        print("Sampling Rate ", self.rate)
        self.chunk = None
        self.audio_data = np.zeros(0)
        self.audio_pos = 0
        self.pos = 0
        self.playing = False
        self.freq = 20
        self.old_freq = self.freq

    def set_freq(self, freq):
        self.old_freq = self.freq
        self.freq = freq

    def end(self):
        self.stop()
        del self.stream
        del self.sample

    @staticmethod
    def get_bytes(chunk):
        # chunk is scaled and converted from float32 to int16 bytes
        return (chunk * 32767).astype('int16').tobytes()
        # return (chunk * 32767).astype('int8').tobytes()

    def render_audio(self, pos, freq):
        start = pos
        end = pos + self.chunk_size
        x_audio = np.arange(start, end) / self.rate
        return np.sin(2*np.pi*freq*x_audio)

    def fade_out(self, signal, length):
        amp_decrease = np.linspace(1, 0, length)
        signal[-length:] *= amp_decrease
        return signal

    def fade_in(self, signal, length):
        amp_increase = np.linspace(0, 1, length)
        signal[:length] *= amp_increase
        return signal

    def run(self):
        self.sample = AudioSample()
        self.stream.add_sample(self.sample)
        self.sample.play()
        self.playing = True
        self.pos = 0

        while self.playing:
            self.chunk = self.render_audio(self.pos, self.old_freq)

            if self.pos <= 0:
                self.chunk = self.fade_in(self.chunk, 256)

            self.pos += self.chunk_size

            if self.freq != self.old_freq:
                self.chunk = self.fade_out(self.chunk, 256)
                self.pos = 0
                self.old_freq = self.freq

            self.write_audio_data()

        self.chunk = self.fade_out(
            self.render_audio(self.pos, self.old_freq), 256)
        self.write_audio_data()
        # self.sample.stop()

    def write_audio_data(self):
        self.audio_data = self.chunk
        self.chunk = self.get_bytes(self.chunk)
        self.sample.write(self.chunk)

    def stop(self):
        self.playing = False

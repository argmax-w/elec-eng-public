# Data

The project leans on exactly one data file, and even then only optionally: a
field recording of a cicada chorus, read by the spectrum section of notebook 04.

## `raw/cicada_kuramoto.wav`

- A single-channel field recording of a cicada chorus, roughly seven megabytes.
- Not committed: WAV files are excluded by the repository `.gitignore`, so on a
  clean checkout this file is absent.
- Used only to compare the dominant call frequency in the recording with the
  natural frequency in the Kuramoto simulation. The simulation needs no audio,
  and notebook 04 detects a missing recording and skips the spectrum with a
  clear message.

### Supplying your own recording

You do not need this exact file. Any mono WAV recording of insects, or any other
near-periodic source, will do. Drop it in at `data/raw/cicada_kuramoto.wav` and
rerun notebook 04. The helper `nldynamics.kuramoto.audio_spectrum` reduces a
stereo file to mono, computes the real-FFT magnitude spectrum and a binned
summary, and reports the dominant peak above DC.

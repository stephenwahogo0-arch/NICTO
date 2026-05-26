import torch
import torch.nn as nn
import torch.nn.functional as F
from neural.config import NeuralConfig

try:
    import torchaudio
    import torchaudio.functional as AF
    HAS_TORCHAUDIO = True
except ImportError:
    HAS_TORCHAUDIO = False


class SpectrogramCNN(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.proj = nn.Linear(128, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.gelu(self.bn1(self.conv1(x)))
        x = F.gelu(self.bn2(self.conv2(x)))
        x = F.gelu(self.bn3(self.conv3(x)))
        x = self.pool(x).flatten(1)
        return self.proj(x)


class AudioEncoder(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_mels = 80
        self.n_fft = 512
        self.hop_length = 160
        self.cnn = SpectrogramCNN(config.d_model)

    def _mel_spectrogram(self, waveform: torch.Tensor, sample_rate: int = 16000) -> torch.Tensor:
        if HAS_TORCHAUDIO:
            mel_spec = AF.melscale_fbanks(
                self.n_fft // 2 + 1, 0, sample_rate, self.n_mels, sample_rate
            )
            spec = torch.stft(
                waveform,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                win_length=self.n_fft,
                window=torch.hann_window(self.n_fft, device=waveform.device),
                return_complex=True,
            )
            mag = spec.abs()
            mel = torch.einsum("...ft,fm->...mt", mag, mel_spec.to(mag.device))
            mel = torch.log(mel.clamp(min=1e-10))
            return mel.unsqueeze(1)
        spec = torch.stft(
            waveform,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.n_fft,
            return_complex=True,
        )
        mag = spec.abs()
        mag = torch.log(mag.clamp(min=1e-10))
        return mag.unsqueeze(1)

    def forward(self, spectrograms: torch.Tensor) -> torch.Tensor:
        return self.cnn(spectrograms)

    def encode(self, audio_path: str) -> torch.Tensor:
        if not HAS_TORCHAUDIO:
            raise ImportError("torchaudio required for audio encoding")
        waveform, sample_rate = torchaudio.load(audio_path)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        if waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        mel = self._mel_spectrogram(waveform, 16000)
        mel = mel.to(next(self.parameters()).device)
        with torch.no_grad():
            return self.forward(mel)

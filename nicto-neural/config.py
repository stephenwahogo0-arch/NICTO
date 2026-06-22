class NeuralConfig:
    d_model: int = 512
    device: str = "cpu"
    vocab_size: int = 32768

    def __init__(self, d_model: int = 512, device: str = "cpu", vocab_size: int = 32768):
        self.d_model = d_model
        self.device = device if device in ("cpu", "cuda") else "cpu"
        self.vocab_size = vocab_size

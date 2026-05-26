import torch
import torch.nn as nn
import torch.nn.functional as F
from neural.config import NeuralConfig

try:
    from torchvision.models import resnet18, ResNet18_Weights
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False

try:
    from PIL import Image
    import torchvision.transforms as T
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class SimpleCNN(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(64)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(256)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.proj = nn.Linear(256, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.gelu(self.bn1(self.conv1(x)))
        x = F.gelu(self.bn2(self.conv2(x)))
        x = F.gelu(self.bn3(self.conv3(x)))
        x = self.pool(x).flatten(1)
        return self.proj(x)


class ImageEncoder(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.d_model = config.d_model
        if HAS_TORCHVISION:
            backbone = resnet18(weights=ResNet18_Weights.DEFAULT)
            self.features = nn.Sequential(*list(backbone.children())[:-2])
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
            self.proj = nn.Linear(512, config.d_model)
        else:
            self.features = SimpleCNN(config.d_model)
            self.proj = nn.Identity()

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        if HAS_TORCHVISION:
            x = self.features(images)
            x = self.pool(x).flatten(1)
            return self.proj(x)
        return self.features(images)

    @staticmethod
    def default_transform(size: int = 224):
        if not HAS_PIL:
            return None
        return T.Compose([
            T.Resize((size, size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def encode(self, image_path: str) -> torch.Tensor:
        if not HAS_PIL:
            raise ImportError("PIL/Pillow required for image encoding")
        transform = self.default_transform()
        if transform is None:
            raise ImportError("torchvision.transforms required for image encoding")
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img).unsqueeze(0).to(next(self.parameters()).device)
        with torch.no_grad():
            return self.forward(img_tensor)

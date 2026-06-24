"""20 coding/programming specialist networks — learn via Unsupervised + RL."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple


class ProgrammingNeuralNet(nn.Module):
    """Base coding specialist — self-supervised pre-train + RL fine-tune."""
    def __init__(self, d_model: int = 256, vocab_size: int = 128, name: str = ""):
        super().__init__()
        self.name = name
        self.emb = nn.Embedding(vocab_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True, activation='gelu')
        self.encoder = nn.TransformerEncoder(encoder_layer, 4)
        self.head = nn.Linear(d_model, vocab_size)
        self.value = nn.Linear(d_model, 1)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.emb(x)
        h = self.encoder(h)
        h = self.norm(h)
        logits = self.head(h)
        v = self.value(h.mean(dim=1))
        return logits, v

    def unsupervised_loss(self, x: torch.Tensor, mask_ratio: float = 0.15) -> torch.Tensor:
        mask = torch.rand_like(x.float()) < mask_ratio
        masked = x.clone()
        masked[mask] = 0
        logits, _ = self.forward(masked)
        loss = F.cross_entropy(logits[mask].view(-1, logits.size(-1)), x[mask].view(-1))
        return loss

    def rl_loss(self, x: torch.Tensor, reward: torch.Tensor) -> torch.Tensor:
        logits, value = self.forward(x)
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        advantage = reward - value
        policy_loss = -(log_prob * advantage.detach()).mean()
        value_loss = F.mse_loss(value, reward)
        return policy_loss + value_loss


class CodePatternDetector(nn.Module):
    """Unsupervised pattern mining from code."""
    def __init__(self, d_model=256):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 3)
        self.proj = nn.Linear(d_model, d_model)

    def forward(self, x):
        return self.proj(self.enc(x).mean(1))


class CodeContrastiveLearner(nn.Module):
    """Contrastive learning for code similarity."""
    def __init__(self, d_model=256):
        super().__init__()
        self.encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 3)
        self.proj = nn.Sequential(nn.Linear(d_model, d_model), nn.GELU(), nn.Linear(d_model, 128))

    def forward(self, x):
        return self.proj(self.encoder(x).mean(1))

    def contrastive_loss(self, z1, z2, temp=0.1):
        z1, z2 = F.normalize(z1, dim=-1), F.normalize(z2, dim=-1)
        sim = z1 @ z2.T / temp
        labels = torch.arange(z1.size(0), device=z1.device)
        return F.cross_entropy(sim, labels) + F.cross_entropy(sim.T, labels)


class CodeRLAgent(nn.Module):
    """RL agent that learns to write code via compiler feedback."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.policy = nn.Linear(d_model, vocab_size)
        self.value = nn.Linear(d_model, 1)

    def forward(self, x):
        h = self.enc(self.emb(x))
        return F.softmax(self.policy(h), dim=-1), self.value(h.mean(1))

    def get_action(self, x, temp=0.8):
        probs, _ = self.forward(x)
        probs = probs[:, -1] / temp
        return torch.multinomial(probs, 1)

    def ppo_loss(self, x, actions, old_log_probs, advantages, returns, clip_eps=0.2):
        probs, values = self.forward(x)
        probs = probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1)
        log_probs = torch.log(probs + 1e-8)
        ratio = torch.exp(log_probs - old_log_probs)
        clipped = torch.clamp(ratio, 1-clip_eps, 1+clip_eps)
        policy_loss = -torch.min(ratio * advantages, clipped * advantages).mean()
        value_loss = F.mse_loss(values.squeeze(-1), returns)
        return policy_loss + 0.5 * value_loss


class CodeInstructionTuner(nn.Module):
    """Supervised fine-tune on instruction-code pairs."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        return self.head(self.enc(self.emb(x)))


class DebugAgent(nn.Module):
    """Finds and fixes bugs via RL from compiler errors."""
    def __init__(self, d_model=256, n_errors=100):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.fix = nn.Linear(d_model, d_model)
        self.head = nn.Linear(d_model, n_errors)

    def forward(self, x):
        return torch.sigmoid(self.head(self.fix(self.enc(x).mean(1))))


class CodeGeneratorNet(nn.Module):
    """Generates code from natural language descriptions."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, src, tgt):
        return self.head(self.dec(self.emb(tgt), self.enc(self.emb(src))))


class CodeReviewer(nn.Module):
    """Reviews code for bugs, style, security."""
    def __init__(self, d_model=256, n_issues=50):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model//2), nn.GELU(), nn.Linear(d_model//2, n_issues), nn.Sigmoid()
        )

    def review(self, x):
        return self.classifier(self.enc(x).mean(1))


class CodeOptimizer(nn.Module):
    """Optimizes code for speed and memory."""
    def __init__(self, d_model=256):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.reg = nn.Linear(d_model, 3)

    def forward(self, x):
        return self.reg(self.enc(x).mean(1))


class APIGenerator(nn.Module):
    """Generates API endpoints and schemas."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.head = nn.Linear(d_model, vocab_size)

    def generate(self, spec, max_len=50):
        tgt = torch.zeros(1, 1, dtype=torch.long)
        h = self.emb(spec).mean(0, keepdim=True).expand(1, 1, -1)
        mem = h
        for _ in range(max_len):
            l = self.dec(self.emb(tgt), mem)
            n = self.head(l[:, -1:]).argmax(-1)
            tgt = torch.cat([tgt, n], -1)
            if n.item() == 0:
                break
        return tgt


class TestGenerator(nn.Module):
    """Generates unit tests for code."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Linear(d_model, vocab_size)

    def generate_tests(self, code, max_len=100):
        h = self.enc(self.emb(code))
        tgt = torch.zeros(1, 1, dtype=torch.long)
        for _ in range(max_len):
            n = self.head(self.dec(self.emb(tgt), h)[:, -1:]).argmax(-1)
            tgt = torch.cat([tgt, n], -1)
            if n.item() == 0:
                break
        return tgt


class RefactoringNet(nn.Module):
    """Refactors code into cleaner patterns."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Linear(d_model, vocab_size)

    def refactor(self, code, max_len=200):
        h = self.enc(self.emb(code))
        tgt = torch.zeros(1, 1, dtype=torch.long)
        for _ in range(max_len):
            n = self.head(self.dec(self.emb(tgt), h)[:, -1:]).argmax(-1)
            tgt = torch.cat([tgt, n], -1)
            if n.item() == 0:
                break
        return tgt


class TypeInferrer(nn.Module):
    """Infers types for untyped code."""
    def __init__(self, d_model=256, n_types=50):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.head = nn.Linear(d_model, n_types)

    def infer(self, x):
        return F.softmax(self.head(self.enc(x).mean(1)), dim=-1)


class DependencyAnalyzer(nn.Module):
    """Analyzes code dependencies and builds graphs."""
    def __init__(self, d_model=256, max_deps=50):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.head = nn.Linear(d_model, max_deps)

    def analyze(self, x):
        return torch.sigmoid(self.head(self.enc(x).mean(1)))


class CodeVectorizer(nn.Module):
    """Converts code to executable vector representation for RL."""
    def __init__(self, d_model=256):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 8)
        self.proj = nn.Linear(d_model, d_model)

    def embed(self, x):
        return self.proj(self.enc(x).mean(1))


class CodeInterpreter(nn.Module):
    """Learns to simulate code execution in latent space."""
    def __init__(self, d_model=256):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.state_proj = nn.Linear(d_model, d_model)
        self.step = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.05, batch_first=True), 4)

    def forward(self, x, n_steps=10):
        h = self.enc(x)
        s = self.state_proj(h.mean(1, keepdim=True))
        for _ in range(n_steps):
            s = self.step(s)
        return s


class CodeExplainer(nn.Module):
    """Explains code in natural language."""
    def __init__(self, d_model=256, vocab_size=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Linear(d_model, vocab_size)

    def explain(self, code, max_len=100):
        h = self.enc(self.emb(code))
        tgt = torch.zeros(1, 1, dtype=torch.long)
        for _ in range(max_len):
            n = self.head(self.dec(self.emb(tgt), h)[:, -1:]).argmax(-1)
            tgt = torch.cat([tgt, n], -1)
            if n.item() == 0:
                break
        return tgt


class SecurityAuditor(nn.Module):
    """Audits code for vulnerabilities using RL-trained patterns."""
    def __init__(self, d_model=256, n_vulns=30):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model//2), nn.GELU(), nn.Linear(d_model//2, n_vulns), nn.Sigmoid()
        )

    def audit(self, x):
        return self.head(self.enc(x).mean(1))


class PerformanceProfiler(nn.Module):
    """Profiles and predicts code performance."""
    def __init__(self, d_model=256):
        super().__init__()
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 4)
        self.reg = nn.Linear(d_model, 3)

    def profile(self, x):
        return self.reg(self.enc(x).mean(1))


class CodeTranslator(nn.Module):
    """Translates code between programming languages."""
    def __init__(self, d_model=256, vocab_size=128, n_langs=10):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, d_model)
        self.lang_emb = nn.Embedding(n_langs, d_model)
        self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model, 4, d_model*2, 0.1, batch_first=True), 6)
        self.head = nn.Linear(d_model, vocab_size)

    def translate(self, code, lang_id, max_len=200):
        h = self.enc(self.emb(code)) + self.lang_emb.weight[lang_id].unsqueeze(0).unsqueeze(0)
        tgt = torch.zeros(1, 1, dtype=torch.long)
        for _ in range(max_len):
            n = self.head(self.dec(self.emb(tgt), h)[:, -1:]).argmax(-1)
            tgt = torch.cat([tgt, n], -1)
            if n.item() == 0:
                break
        return tgt


# All 20 coding specialists
CODING_SPECIALISTS = {
    "code_pattern_detector": CodePatternDetector,
    "code_contrastive_learner": CodeContrastiveLearner,
    "code_rl_agent": CodeRLAgent,
    "code_instruction_tuner": CodeInstructionTuner,
    "debug_agent": DebugAgent,
    "code_generator": CodeGeneratorNet,
    "code_reviewer": CodeReviewer,
    "code_optimizer": CodeOptimizer,
    "api_generator": APIGenerator,
    "test_generator": TestGenerator,
    "refactoring_net": RefactoringNet,
    "type_inferrer": TypeInferrer,
    "dependency_analyzer": DependencyAnalyzer,
    "code_vectorizer": CodeVectorizer,
    "code_interpreter": CodeInterpreter,
    "code_explainer": CodeExplainer,
    "security_auditor": SecurityAuditor,
    "performance_profiler": PerformanceProfiler,
    "code_translator": CodeTranslator,
    "programming_net": ProgrammingNeuralNet,
}

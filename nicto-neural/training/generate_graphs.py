"""Generate NICTO training performance graphs from training_metrics.json."""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_PATH = os.path.join(SCRIPT_DIR, "training_metrics.json")
OUTPUT_DIR = SCRIPT_DIR


def smooth(values, window=10):
    """Simple moving average smoothing."""
    if len(values) < window:
        return values
    smoothed = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        smoothed.append(sum(values[start:i+1]) / (i - start + 1))
    return smoothed


def load_metrics():
    with open(METRICS_PATH) as f:
        return json.load(f)


def generate_main_performance_graph(metrics):
    """6-panel performance graph."""
    fig = plt.figure(figsize=(20, 24))
    fig.suptitle(
        "NICTO Neural Core V1 — Training Performance (17B Architecture)",
        fontsize=18, fontweight="bold", y=0.98,
    )
    fig.text(
        0.5, 0.96,
        f"200 Epochs × 10 Tasks/Epoch = {metrics['total_tasks']} Tasks | "
        f"Training Time: {metrics['training_time_seconds']:.1f}s",
        ha="center", fontsize=12, color="gray",
    )

    gs = gridspec.GridSpec(3, 2, hspace=0.35, wspace=0.3, top=0.94, bottom=0.04)
    epochs = metrics["epochs"]

    # ── Panel 1: Reward curve ──
    ax1 = fig.add_subplot(gs[0, 0])
    raw_reward = metrics["avg_reward"]
    smoothed_reward = smooth(raw_reward, 15)
    ax1.plot(epochs, raw_reward, alpha=0.2, color="#4A90D9", linewidth=0.8)
    ax1.plot(epochs, smoothed_reward, color="#4A90D9", linewidth=2.5, label="Avg Reward (smoothed)")
    ax1.axhline(y=raw_reward[0], color="red", linestyle="--", alpha=0.5, label=f"Initial: {raw_reward[0]:.1f}")
    ax1.axhline(y=raw_reward[-1], color="green", linestyle="--", alpha=0.5, label=f"Final: {raw_reward[-1]:.1f}")
    ax1.fill_between(epochs, raw_reward, alpha=0.05, color="#4A90D9")
    ax1.set_title("Average Reward per Epoch", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Reward")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.3)
    improvement = ((raw_reward[-1] - raw_reward[0]) / max(abs(raw_reward[0]), 0.01)) * 100
    ax1.annotate(
        f"+{improvement:.0f}% improvement",
        xy=(len(epochs)*0.7, smoothed_reward[-1]),
        fontsize=11, fontweight="bold", color="green",
    )

    # ── Panel 2: PPO Training Losses ──
    ax2 = fig.add_subplot(gs[0, 1])
    policy_loss = smooth(metrics["policy_loss"], 10)
    value_loss = smooth(metrics["value_loss"], 10)
    entropy = smooth(metrics["entropy"], 10)
    ax2.plot(epochs, policy_loss, color="#E74C3C", linewidth=2, label="Policy Loss")
    ax2.plot(epochs, entropy, color="#2ECC71", linewidth=2, label="Entropy")
    ax2_twin = ax2.twinx()
    ax2_twin.plot(epochs, value_loss, color="#F39C12", linewidth=2, label="Value Loss", linestyle="--")
    ax2_twin.set_ylabel("Value Loss", color="#F39C12")
    ax2.set_title("PPO Training Losses", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Policy Loss / Entropy")
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: ELO Ratings per Brain ──
    ax3 = fig.add_subplot(gs[1, 0])
    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C"]
    for i, (brain, ratings) in enumerate(metrics["elo_ratings"].items()):
        smoothed = smooth(ratings, 10)
        ax3.plot(epochs, smoothed, color=colors[i % len(colors)], linewidth=2, label=brain.capitalize())
    ax3.axhline(y=1500, color="gray", linestyle=":", alpha=0.5, label="Baseline (1500)")
    ax3.set_title("ELO Ratings by Brain (Average Across Domains)", fontsize=13, fontweight="bold")
    ax3.set_xlabel("Epoch")
    ax3.set_ylabel("ELO Rating")
    ax3.legend(loc="lower right", fontsize=9, ncol=2)
    ax3.grid(True, alpha=0.3)
    final_avg_elo = np.mean([r[-1] for r in metrics["elo_ratings"].values()])
    ax3.annotate(
        f"Avg Final ELO: {final_avg_elo:.0f} (+{final_avg_elo-1500:.0f})",
        xy=(len(epochs)*0.5, final_avg_elo),
        fontsize=11, fontweight="bold", color="#2ECC71",
    )

    # ── Panel 4: Domain Accuracy ──
    ax4 = fig.add_subplot(gs[1, 1])
    domain_colors = plt.cm.tab10(np.linspace(0, 1, len(metrics["domain_accuracy"])))
    for i, (domain, acc) in enumerate(metrics["domain_accuracy"].items()):
        if any(a > 0 for a in acc):
            smoothed = smooth(acc, 15)
            ax4.plot(epochs, smoothed, color=domain_colors[i], linewidth=1.8, label=domain.capitalize())
    ax4.axhline(y=0.75, color="red", linestyle="--", alpha=0.4, label="Curriculum threshold (75%)")
    ax4.set_title("Accuracy by Domain", fontsize=13, fontweight="bold")
    ax4.set_xlabel("Epoch")
    ax4.set_ylabel("Accuracy")
    ax4.set_ylim(0, 1.05)
    ax4.legend(loc="lower right", fontsize=8, ncol=2)
    ax4.grid(True, alpha=0.3)

    # ── Panel 5: Curriculum Progression ──
    ax5 = fig.add_subplot(gs[2, 0])
    curriculum = metrics["curriculum_levels"]
    max_possible = 6 * 10 * 5  # 6 brains × 10 domains × 5 max level
    ax5.plot(epochs, curriculum, color="#8E44AD", linewidth=2.5)
    ax5.fill_between(epochs, curriculum, alpha=0.15, color="#8E44AD")
    ax5.axhline(y=max_possible, color="gold", linestyle="--", alpha=0.5, label=f"Max possible: {max_possible}")
    ax5.set_title("Curriculum Progression (Total Levels Unlocked)", fontsize=13, fontweight="bold")
    ax5.set_xlabel("Epoch")
    ax5.set_ylabel("Total Curriculum Levels")
    ax5.legend(loc="upper left", fontsize=9)
    ax5.grid(True, alpha=0.3)
    pct = (curriculum[-1] / max_possible) * 100
    ax5.annotate(
        f"{curriculum[-1]}/{max_possible} ({pct:.0f}%)",
        xy=(len(epochs)*0.7, curriculum[-1]),
        fontsize=12, fontweight="bold", color="#8E44AD",
    )

    # ── Panel 6: Consistency & Confidence ──
    ax6 = fig.add_subplot(gs[2, 1])
    consistency = smooth(metrics["consistency_sigma"], 15)
    confidence = smooth(metrics["avg_confidence"], 15)
    boost_conf = smooth(metrics["brainboost_confidence"], 15)
    ax6.plot(epochs, consistency, color="#E74C3C", linewidth=2, label="Consistency σ")
    ax6.plot(epochs, confidence, color="#3498DB", linewidth=2, label="Avg Confidence")
    ax6.plot(epochs, boost_conf, color="#2ECC71", linewidth=2, linestyle="--", label="BrainBoost Confidence")
    ax6.set_title("Consistency & Confidence Metrics", fontsize=13, fontweight="bold")
    ax6.set_xlabel("Epoch")
    ax6.set_ylabel("Score")
    ax6.set_ylim(0, 1.1)
    ax6.legend(loc="lower right", fontsize=9)
    ax6.grid(True, alpha=0.3)

    path = os.path.join(OUTPUT_DIR, "performance_graph.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Main performance graph saved: {path}")
    return path


def generate_comparison_graph(metrics):
    """Bar chart comparing NICTO vs other AI models."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle(
        "NICTO vs Other AI Models — Architecture & Capability Comparison",
        fontsize=16, fontweight="bold",
    )

    # ── Panel 1: Parameter Count ──
    models = ["GPT-4\n(~1.8T MoE)", "Claude 3.5\n(est. ~175B)", "Llama 3\n70B",
              "Gemini Pro\n(est. ~540B)", "Mistral\n7B", "NICTO\n17B"]
    params = [1800, 175, 70, 540, 7, 17]
    colors = ["#95A5A6"] * 5 + ["#E74C3C"]
    axes[0].barh(models, params, color=colors, edgecolor="white", linewidth=1.5)
    axes[0].set_xlabel("Parameters (Billions)", fontsize=11)
    axes[0].set_title("Parameter Count", fontsize=13, fontweight="bold")
    for i, v in enumerate(params):
        axes[0].text(v + 20, i, f"{v}B", va="center", fontsize=10, fontweight="bold")
    axes[0].set_xlim(0, max(params) * 1.2)

    # ── Panel 2: Architecture Features ──
    features = [
        "Multi-Brain\nSystem", "Self-Training\n(PPO RL)", "ELO\nRating",
        "Curriculum\nLearning", "Reward Hacking\nDetection", "BrainBoost\nEnsemble",
    ]
    nicto_scores = [6, 1, 1, 1, 1, 1]  # NICTO has all
    gpt4_scores = [0, 0, 0, 0, 0, 0]  # GPT-4: none of these (external system)
    llama_scores = [0, 0, 0, 0, 0, 0]
    x = np.arange(len(features))
    width = 0.25
    axes[1].bar(x - width, nicto_scores, width, label="NICTO 17B", color="#E74C3C")
    axes[1].bar(x, gpt4_scores, width, label="GPT-4", color="#3498DB")
    axes[1].bar(x + width, llama_scores, width, label="Llama 3 70B", color="#2ECC71")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(features, fontsize=8)
    axes[1].set_ylabel("Has Feature (1=Yes)")
    axes[1].set_title("Unique Architecture Features", fontsize=13, fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].set_ylim(0, 8)
    for i, v in enumerate(nicto_scores):
        label = str(v) if v > 1 else ("Y" if v == 1 else "N")
        axes[1].text(i - width, v + 0.1, label, ha="center", fontsize=9, fontweight="bold", color="#E74C3C")

    # ── Panel 3: Training Metrics (NICTO final) ──
    metric_names = [
        "Avg Reward\n(final)", "Curriculum\n(% unlocked)", "ELO\n(avg gain)",
        "Consistency σ", "Policy Loss\n(convergence)", "Tasks\nProcessed",
    ]
    final_reward = metrics["avg_reward"][-1]
    max_possible = 6 * 10 * 5
    curriculum_pct = (metrics["curriculum_levels"][-1] / max_possible) * 100
    final_avg_elo_gain = np.mean([r[-1] for r in metrics["elo_ratings"].values()]) - 1500
    final_consistency = metrics["consistency_sigma"][-1]
    final_policy = abs(metrics["policy_loss"][-1])

    values = [final_reward, curriculum_pct, final_avg_elo_gain, final_consistency * 100, (1 - final_policy) * 100, metrics["total_tasks"] / 20]
    bar_colors = ["#4A90D9", "#8E44AD", "#2ECC71", "#E74C3C", "#F39C12", "#1ABC9C"]
    bars = axes[2].bar(metric_names, values, color=bar_colors, edgecolor="white", linewidth=1.5)
    axes[2].set_title("NICTO Final Training Metrics", fontsize=13, fontweight="bold")
    axes[2].set_ylabel("Score / Percentage")
    for bar, v in zip(bars, values):
        axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                     f"{v:.1f}", ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "comparison_graph.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Comparison graph saved: {path}")
    return path


def generate_elo_heatmap(metrics):
    """ELO rating heatmap: brains × time."""
    fig, ax = plt.subplots(figsize=(16, 5))

    brains = list(metrics["elo_ratings"].keys())
    epochs = metrics["epochs"]

    # Sample every 5th epoch for readability
    sample_indices = list(range(0, len(epochs), 5))
    sampled_epochs = [epochs[i] for i in sample_indices]

    data = np.array([
        [metrics["elo_ratings"][brain][i] for i in sample_indices]
        for brain in brains
    ])

    im = ax.imshow(data, aspect="auto", cmap="RdYlGn", interpolation="bilinear")
    ax.set_yticks(range(len(brains)))
    ax.set_yticklabels([b.capitalize() for b in brains], fontsize=11)

    tick_positions = list(range(0, len(sampled_epochs), 5))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([str(sampled_epochs[i]) for i in tick_positions], fontsize=9)
    ax.set_xlabel("Epoch", fontsize=11)
    ax.set_title("ELO Rating Evolution — All Brains (Heatmap)", fontsize=14, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("ELO Rating", fontsize=11)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "elo_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"ELO heatmap saved: {path}")
    return path


if __name__ == "__main__":
    print("Loading training metrics...")
    metrics = load_metrics()
    print(f"Loaded {len(metrics['epochs'])} epochs of data")
    print()

    p1 = generate_main_performance_graph(metrics)
    p2 = generate_comparison_graph(metrics)
    p3 = generate_elo_heatmap(metrics)

    print(f"\nAll graphs generated in: {OUTPUT_DIR}")

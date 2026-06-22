"""Inject game engine mastery into KYROS's training system."""
import sys, json, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

data_path = os.path.join(os.path.dirname(__file__), "..", "training", "game_engine_mastery.json")
with open(data_path) as f:
    training_data = json.load(f)

from kyros.training.hourly import HourlyTrainer
import tempfile

td = tempfile.mkdtemp()
trainer = HourlyTrainer(data_dir=td)

print("Injecting {} game engine mastery conversations...".format(len(training_data)))
for i, item in enumerate(training_data):
    conv = item["conversation"]
    user_msg = conv[0]["content"]
    assistant_msg = conv[1]["content"]
    trainer.record_interaction(user_msg, assistant_msg, duration=random.uniform(1.0, 5.0))
    if (i + 1) % 5 == 0:
        print("  Injected {}/{}...".format(i + 1, len(training_data)))

print("\nRunning training on all recorded data...")
result = trainer.train()
print("Training result: {}".format(result))

stats = trainer.get_stats()
print("\nTraining Stats:")
print("  Total patterns: {}".format(stats.get("total_patterns", 0)))
print("  Total conversations: {}".format(stats.get("total_conversations", 0)))
print("  Training sessions: {}".format(stats.get("training_sessions", 0)))
print("  Topics: {}".format(stats.get("topics", [])))

print("\nKYROS game engine mastery training complete!")

"""Generate sample personalized sprite from reference images."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "kyros-core", "src"))

from kyros.avatar.personalize import PersonalAvatarGenerator

pag = PersonalAvatarGenerator()
img = pag.generate_lively_sprite("idle", "happy", 0)
path = "kyros_sample_sprite.png"
img.save(path)
size = os.path.getsize(path)
print(f"Saved: {path} ({size} bytes)")

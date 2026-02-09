import pygame
import json
import os
import sys

# Import your renderer
from data.renderers import Renderer

def load_characters():
    """Load all character JSON files from data/characters/"""
    cast = {}
    path = "data/characters"
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), "r") as f:
                data = json.load(f)
                cast[data["id"]] = data
    return cast

def load_assets():
    """Load all image assets from data/assets/ (recursive)"""
    gallery = {}
    path = "data/assets"
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith((".png", ".jpg", ".jpeg", "webp")):
                name = os.path.splitext(filename)[0]
                full_path = os.path.join(root, filename)
                img = pygame.image.load(full_path).convert_alpha()
                gallery[name] = img
    return gallery

def load_chapter(chapter_num):
    """Load a specific chapter's story data"""
    chapter_file = f"data/story/chapter_{chapter_num}.json"
    if os.path.exists(chapter_file):
        with open(chapter_file, "r") as f:
            return json.load(f)
    else:
        print(f"Warning: {chapter_file} not found!")
        return None

def main():
    # --- INITIALIZATION ---
    pygame.init()
    
    # Load Config
    with open("game_config.json", "r") as f:
        config = json.load(f)
    
    screen = pygame.display.set_mode((config["window"]["width"], config["window"]["height"]))
    pygame.display.set_caption(config["window"]["caption"])
    clock = pygame.time.Clock()
    
    # --- DATA LOADING ---
    cast = load_characters()
    images = load_assets()
    
    # --- GAME STATE ---
    renderer = Renderer(screen)
    current_chapter = config["engine_settings"]["start_chapter"]
    story = load_chapter(current_chapter)
    
    if not story:
        print("Failed to load initial chapter!")
        pygame.quit()
        sys.exit()
    
    current_scene_id = list(story.keys())[0]  # Start with first scene
    running = True
    
    # Typewriter effect variables
    text_speed = config["engine_settings"]["text_speed"]
    current_text_len = 0
    text_timer = 0

    # --- MAIN GAME LOOP ---
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        scene = story[current_scene_id]
        speaker_id = scene["speaker"]
        speaker_data = cast.get(speaker_id, {"name": "Unknown", "images": {}})
        
        # Get the correct image based on the emotion in the story JSON
        emotion = scene.get("sprites", "default")
        sprite_key = speaker_data["images"].get(emotion)
        current_sprite = images.get(sprite_key) if sprite_key else None
        
        # Get background
        current_bg = images.get(scene.get("bg_image"))

        # 1. EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If text is still typing, show all text immediately
                if current_text_len < len(scene["text"]):
                    current_text_len = len(scene["text"])
                # Otherwise, move to next scene
                else:
                    if "next_scene" in scene:
                        next_scene = scene["next_scene"]
                        
                        # Check if it's a chapter transition
                        if next_scene.startswith("chapter_"):
                            # Extract chapter number (e.g., "chapter_2" -> 2)
                            next_chapter = int(next_scene.split("_")[1])
                            story = load_chapter(next_chapter)
                            if story:
                                current_chapter = next_chapter
                                current_scene_id = list(story.keys())[0]
                                current_text_len = 0
                                text_timer = 0
                            else:
                                print(f"Chapter {next_chapter} not found!")
                                running = False
                        else:
                            # Regular scene transition
                            current_scene_id = next_scene
                            current_text_len = 0
                            text_timer = 0
                    else:
                        print("End of Chapter!")
                        running = False
            
            # Debug: Press SPACE to skip to next chapter
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and config["engine_settings"]["debug_mode"]:
                    print(f"Debug: Skipping to next chapter")
                    story = load_chapter(current_chapter + 1)
                    if story:
                        current_chapter += 1
                        current_scene_id = list(story.keys())[0]
                        current_text_len = 0
                        text_timer = 0

        # 2. UPDATE TYPEWRITER EFFECT
        if current_text_len < len(scene["text"]):
            text_timer += dt
            if text_timer >= text_speed:
                current_text_len += 1
                text_timer = 0

        # 3. DRAWING
        renderer.draw_scene(
            scene_text=scene["text"],
            speaker_name=speaker_data["name"],
            sprite=current_sprite,
            background=current_bg,
            current_text_len=int(current_text_len)
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
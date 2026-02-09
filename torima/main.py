import pygame
import json
import os
import sys

# Import your renderer - Updated path
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

def load_story_file(filepath):
    """Load any story JSON file (chapter or ending)"""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        print(f"Warning: {filepath} not found!")
        return None

def load_chapter(chapter_filename):
    """Load a specific chapter's story data"""
    return load_story_file(f"data/story/chapters/{chapter_filename}.json")

def load_ending(ending_filename):
    """Load an ending file"""
    return load_story_file(f"data/story/endings/{ending_filename}")

class GameState:
    """Manages game state including scores, current story, and scene"""
    def __init__(self, config):
        self.scores = config["engine_settings"]["initial_scores"].copy()
        self.current_story = None
        self.current_scene_id = None
        self.current_chapter = config["engine_settings"]["start_chapter"]
        self.is_in_ending = False
        
    def update_scores(self, score_changes):
        """Update scores based on player choices"""
        for stat, value in score_changes.items():
            self.scores[stat] = self.scores.get(stat, 0) + value
    
    def check_requirements(self, requirements):
        """Check if current scores meet requirements"""
        for stat, needed in requirements.items():
            if self.scores.get(stat, 0) < needed:
                return False
        return True
    
    def load_story(self, story_data, scene_id="start"):
        """Load new story data and set starting scene"""
        self.current_story = story_data
        self.current_scene_id = scene_id
    
    def get_current_scene(self):
        """Get the current scene data"""
        if self.current_story and self.current_scene_id:
            return self.current_story.get(self.current_scene_id)
        return None

def evaluate_score_check(game_state, scene):
    """Evaluate score check and return next destination"""
    conditions = scene.get("conditions", [])
    
    # Check conditions in order (highest requirements first)
    for condition in conditions:
        requirement = condition.get("requirement", {})
        if game_state.check_requirements(requirement):
            return {
                "next_file": condition.get("next_file"),
                "next_scene": condition.get("next_scene", "start")
            }
    
    # Return default if no conditions met
    return {
        "next_file": scene.get("default_file"),
        "next_scene": scene.get("default_scene", "start")
    }

def evaluate_checkpoint(game_state, scene):
    """Evaluate checkpoint and determine pass/fail"""
    requirements = scene.get("requirements", {})
    
    if game_state.check_requirements(requirements):
        # Passed checkpoint
        return {
            "next_file": scene.get("pass_file"),
            "next_scene": scene.get("pass_scene", "start")
        }
    else:
        # Failed checkpoint - bad ending
        return {
            "next_file": scene.get("fail_file"),
            "next_scene": scene.get("fail_scene", "start")
        }

def navigate_to_scene(game_state, destination, config):
    """Navigate to the next scene, handling file loading if needed"""
    next_file = destination.get("next_file")
    next_scene = destination.get("next_scene")
    
    # Load new file if specified
    if next_file:
        if next_file.endswith(".end"):
            # Load from endings directory
            new_story = load_ending(next_file)
            game_state.is_in_ending = True
        else:
            new_story = load_chapter(next_file)
            game_state.current_chapter = next_file
            game_state.is_in_ending = False
        
        if new_story:
            game_state.load_story(new_story, next_scene)
        else:
            print(f"Failed to load: {next_file}")
    
    # Just change scene within current file
    elif next_scene:
        # Check if it's a chapter transition (e.g., "chapter_2")
        if next_scene.startswith("chapter_"):
            chapter_num = int(next_scene.split("_")[1])
            story = load_chapter(chapter_num)
            if story:
                game_state.current_chapter = chapter_num
                game_state.load_story(story, list(story.keys())[0])
                game_state.is_in_ending = False
            else:
                print(f"Chapter {chapter_num} not found!")
        else:
            # Regular scene change within same file
            game_state.current_scene_id = next_scene

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
    game_state = GameState(config)
    
    # Load initial chapter
    story = load_chapter(game_state.current_chapter)
    if not story:
        print("Failed to load initial chapter!")
        pygame.quit()
        sys.exit()
    
    game_state.load_story(story, list(story.keys())[0])
    
    running = True
    
    # Typewriter effect variables
    text_speed = config["engine_settings"]["text_speed"]
    current_text_len = 0
    text_timer = 0
    
    # Choice handling
    waiting_for_choice = False
    current_choices = []
    choice_rects = []
    hover_index = -1

    # --- MAIN GAME LOOP ---
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        scene = game_state.get_current_scene()
        if not scene:
            print("No valid scene!")
            running = False
            continue
        
        # Get speaker data
        speaker_id = scene.get("speaker")
        speaker_data = cast.get(speaker_id, {"name": "", "images": {}}) if speaker_id else {"name": "", "images": {}}
        
        # Get the correct image based on the emotion in the story JSON
        emotion = scene.get("sprite_emotion", "default")
        sprite_key = speaker_data["images"].get(emotion)
        current_sprite = images.get(sprite_key) if sprite_key else None
        
        # Get background
        current_bg = images.get(scene.get("bg_image"))

        # 1. EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEMOTION:
                if waiting_for_choice:
                    # Check which choice is being hovered
                    hover_index = -1
                    mouse_pos = event.pos
                    for i, rect in enumerate(choice_rects):
                        if rect.collidepoint(mouse_pos):
                            hover_index = i
                            break
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Handle choice selection
                if waiting_for_choice:
                    mouse_pos = event.pos
                    clicked_index = -1
                    
                    for i, rect in enumerate(choice_rects):
                        if rect.collidepoint(mouse_pos):
                            clicked_index = i
                            break
                    
                    if clicked_index != -1:
                        selected_choice = current_choices[clicked_index]
                        
                        # Update scores if choice has score changes
                        if "score_change" in selected_choice:
                            game_state.update_scores(selected_choice["score_change"])
                            if config["engine_settings"]["debug_mode"]:
                                print(f"Scores updated: {game_state.scores}")
                        
                        # Clear choices and advance to next scene
                        waiting_for_choice = False
                        current_choices = []
                        choice_rects = []
                        hover_index = -1
                        current_text_len = 0
                        text_timer = 0
                        
                        # Navigate to next scene
                        next_destination = {
                            "next_file": selected_choice.get("next_file"),
                            "next_scene": selected_choice.get("next_scene")
                        }
                        navigate_to_scene(game_state, next_destination, config)
                
                # Regular text advance
                elif not waiting_for_choice:
                    # If text is still typing, show all text immediately
                    if current_text_len < len(scene.get("text", "")):
                        current_text_len = len(scene.get("text", ""))
                    # Otherwise, process scene progression
                    else:
                        # Check for choices
                        if "choices" in scene:
                            current_choices = scene["choices"]
                            choice_rects = renderer.get_choice_rects(len(current_choices))
                            waiting_for_choice = True
                        # Check for special scene types
                        elif scene.get("type") == "score_check":
                            next_destination = evaluate_score_check(game_state, scene)
                            navigate_to_scene(game_state, next_destination, config)
                            current_text_len = 0
                            text_timer = 0
                        elif scene.get("type") == "checkpoint":
                            next_destination = evaluate_checkpoint(game_state, scene)
                            navigate_to_scene(game_state, next_destination, config)
                            current_text_len = 0
                            text_timer = 0
                        elif scene.get("type") == "ending":
                            print(f"THE END: {scene.get('ending_name', 'Unknown Ending')}")
                            print(f"Final Scores: {game_state.scores}")
                            running = False
                        # Regular scene progression
                        elif "next_scene" in scene:
                            next_destination = {"next_scene": scene["next_scene"]}
                            navigate_to_scene(game_state, next_destination, config)
                            current_text_len = 0
                            text_timer = 0
                        else:
                            print("End of story!")
                            running = False
            
            # Debug: Press SPACE to skip to next chapter
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and config["engine_settings"]["debug_mode"]:
                    print(f"Debug: Skipping to next chapter")
                    story = load_chapter(game_state.current_chapter + 1)
                    if story:
                        game_state.current_chapter += 1
                        game_state.load_story(story, list(story.keys())[0])
                        current_text_len = 0
                        text_timer = 0
                
                # Debug: Press 'S' to show scores
                if event.key == pygame.K_s and config["engine_settings"]["debug_mode"]:
                    print(f"Current Scores: {game_state.scores}")

        # 2. UPDATE TYPEWRITER EFFECT (only if not waiting for choice)
        if not waiting_for_choice and current_text_len < len(scene.get("text", "")):
            text_timer += dt
            if text_timer >= text_speed:
                current_text_len += 1
                text_timer = 0

        # 3. DRAWING
        renderer.draw_scene(
            scene_text=scene.get("text", ""),
            speaker_name=speaker_data["name"],
            sprite=current_sprite,
            background=current_bg,
            current_text_len=int(current_text_len)
        )
        
        # Draw choices if waiting for choice
        if waiting_for_choice:
            renderer.draw_choices(current_choices, hover_index)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
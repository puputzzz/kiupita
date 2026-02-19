import pygame, json, os, sys
from data.renderers import Renderer

class GameState:
    def __init__(self, config):
        self.scores = config["engine_settings"]["initial_scores"].copy()
        self.current_chapter = config["engine_settings"]["start_chapter"]
        self.current_scene_id = "start"
        self.story_data = {}

    def load_story(self, data, start_scene):
        self.story_data = data
        self.current_scene_id = start_scene

    def get_current_scene(self):
        return self.story_data.get(self.current_scene_id, {})

def load_characters():
    cast = {}
    path = "data/characters"
    if os.path.exists(path):
        for filename in os.listdir(path):
            if filename.endswith(".json"):
                with open(os.path.join(path, filename), "r") as f:
                    data = json.load(f)
                    cast[data["id"]] = data
    return cast

def load_assets():
    gallery = {}
    path = "data/assets"
    for root, _, files in os.walk(path):
        for filename in files:
            if filename.endswith((".png", ".jpg", ".jpeg")):
                name = os.path.splitext(filename)[0]
                gallery[name] = pygame.image.load(os.path.join(root, filename)).convert_alpha()
    return gallery

def main():
    pygame.init()
    with open("game_config.json", "r") as f:
        config = json.load(f)

    screen = pygame.display.set_mode((config["window"]["width"], config["window"]["height"]))
    clock = pygame.time.Clock()
    cast, assets, renderer = load_characters(), load_assets(), Renderer(screen)
    game_state = GameState(config)

    with open(f"data/story/chapters/{game_state.current_chapter}.json", "r") as f:
        game_state.load_story(json.load(f), "start")

    current_text_len, text_timer = 0, 0
    running = True
    is_fading = False # Defaults to False
    hover_index = -1

    while running:
        dt = clock.tick(60) / 1000.0
        scene = game_state.get_current_scene()
        choices = scene.get("choices", [])
        raw_text = scene.get("text", "")
        clean_text = raw_text.replace("|", "")
        
        waiting_for_choice = (len(choices) > 0 and current_text_len >= len(clean_text))

        # Handle Hover
        mouse_pos = pygame.mouse.get_pos()
        hover_index = -1
        if waiting_for_choice:
            for i, rect in enumerate(renderer.get_choice_rects(len(choices))):
                if rect.collidepoint(mouse_pos): hover_index = i

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if waiting_for_choice and hover_index != -1:
                    choice = choices[hover_index]
                    for stat, val in choice.get("score_change", {}).items():
                        game_state.scores[stat] += val
                    game_state.current_scene_id = choice["next_scene"]
                    current_text_len = 0
                    # ONLY FADE IF NEW SCENE SAYS SO
                    is_fading = game_state.get_current_scene().get("fade", False)
                elif not waiting_for_choice:
                    if current_text_len < len(clean_text):
                        current_text_len = len(clean_text)
                    elif "next_scene" in scene:
                        game_state.current_scene_id = scene["next_scene"]
                        current_text_len = 0
                        # ONLY FADE IF NEW SCENE SAYS SO
                        is_fading = game_state.get_current_scene().get("fade", False)

        # Typewriter Logic
        if not waiting_for_choice and current_text_len < len(clean_text):
            text_timer += dt
            char_idx = min(current_text_len, len(raw_text)-1)
            speed = 0.5 if raw_text[char_idx] == "|" else scene.get("text_speed", config["engine_settings"]["text_speed"])
            if text_timer >= speed:
                current_text_len += 1
                text_timer = 0
        
        # STOP FADING once text starts appearing
        if current_text_len > 1:
            is_fading = False

        # Render
        speaker_id = scene.get("speaker", "???")
        speaker_data = cast.get(speaker_id, {"name": speaker_id, "images": {}})
        renderer.draw_scene(
            raw_text, speaker_data["name"], 
            assets.get(speaker_data["images"].get(scene.get("sprite_emotion", "default"))), 
            assets.get(scene.get("bg_image")), 
            current_text_len, scene.get("zoom", 1.0), is_fading
        )
        
        if waiting_for_choice:
            renderer.draw_choices(choices, hover_index)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__": main()
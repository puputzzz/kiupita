import pygame

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 24)
        self.name_font = pygame.font.SysFont("Arial", 30, bold=True)
        self.choice_font = pygame.font.SysFont("Arial", 26)
        
        # --- DYNAMIC SPRITE BOUNDARIES ---
        # We leave 400px of horizontal room and enough vertical room to stay above the textbox
        self.sprite_max_width = 1000 
        self.sprite_max_height = 500 # Adjusted to prevent head-chopping
        self.sprite_y_offset = self.screen.get_height() - 180
        
        # Fade Transition Variables
        self.fade_surface = pygame.Surface((screen.get_width(), screen.get_height()))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 0 
        self.fade_speed = 12 

        # Choice UI Settings (Fixed button size for choices)
        self.choice_width = 600
        self.choice_height = 50
        self.choice_spacing = 15

    def wrap_text(self, text, max_width):
        """Word wrap helper so text stays inside the box."""
        words = text.split(' ')
        lines, current_line = [], []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.font.size(test_line)[0] < max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines

    def fit_sprite_to_boundary(self, sprite, zoom_factor=1.0):
        original_width, original_height = sprite.get_size()
        # Scale proportionally so it fits within the dynamic box
        scale = min(self.sprite_max_width / original_width, self.sprite_max_height / original_height)
        final_scale = scale * zoom_factor
        return pygame.transform.smoothscale(sprite, (int(original_width * final_scale), int(original_height * final_scale)))

    def draw_scene(self, scene_text, speaker_name, sprite, background, current_text_len, zoom=1.0, is_fading=False):
        # 1. Background
        if background:
            self.screen.blit(pygame.transform.scale(background, self.screen.get_size()), (0, 0))
        else:
            self.screen.fill((0, 0, 0))

        # 2. Sprite
        if sprite:
            zoomed_sprite = self.fit_sprite_to_boundary(sprite, zoom)
            x = (self.screen.get_width() - zoomed_sprite.get_width()) // 2
            # Sit perfectly on top of the textbox
            y = self.screen.get_height() - zoomed_sprite.get_height() - 180 
            self.screen.blit(zoomed_sprite, (x, y))

        # 3. Textbox
        box_width = self.screen.get_width() - 100
        box_rect = pygame.Rect(50, self.screen.get_height() - 180, box_width, 160)
        pygame.draw.rect(self.screen, (20, 20, 20, 230), box_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 2)

        # 4. Text (with Word Wrap)
        clean_text = scene_text.replace("|", "")
        visible_text = clean_text[:current_text_len]
        
        name_surf = self.name_font.render(speaker_name, True, (255, 215, 0))
        self.screen.blit(name_surf, (80, self.screen.get_height() - 170))
        
        wrapped_lines = self.wrap_text(visible_text, box_width - 60)
        for i, line in enumerate(wrapped_lines):
            line_surf = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(line_surf, (80, self.screen.get_height() - 125 + (i * 30)))

        # 5. Fade logic
        if is_fading: self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
        else: self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
        if self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))

    def draw_choices(self, choices, hover_index):
        """Draw choice buttons when dialogue is finished."""
        start_y = (self.screen.get_height() // 2) - (len(choices) * (self.choice_height + self.choice_spacing) // 2)
        for i, choice in enumerate(choices):
            rect = pygame.Rect((self.screen.get_width() - self.choice_width) // 2, 
                               start_y + i * (self.choice_height + self.choice_spacing), 
                               self.choice_width, self.choice_height)
            color = (70, 70, 70) if i == hover_index else (40, 40, 40)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            
            text_surf = self.choice_font.render(choice["text"], True, (255, 255, 255))
            self.screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

    def get_choice_rects(self, num_choices):
        """Helper for mouse collision detection in main.py."""
        start_y = (self.screen.get_height() // 2) - (num_choices * (self.choice_height + self.choice_spacing) // 2)
        return [pygame.Rect((self.screen.get_width() - self.choice_width) // 2, 
                            start_y + i * (self.choice_height + self.choice_spacing), 
                            self.choice_width, self.choice_height) for i in range(num_choices)]
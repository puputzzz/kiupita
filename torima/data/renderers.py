import pygame

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 24)
        self.name_font = pygame.font.SysFont("Arial", 30, bold=True)
        
        # UI Assets - Fixed path to match your folder structure
        try:
            self.textbox = pygame.image.load("data/assets/ui/textbox.png").convert_alpha()
        except FileNotFoundError:
            # Create a fallback textbox if image doesn't exist
            self.textbox = pygame.Surface((1180, 200))
            self.textbox.fill((0, 0, 0))
            self.textbox.set_alpha(180)
        
    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surf = font.render(test_line, True, (255, 255, 255))
            
            if test_surf.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def draw_scene(self, scene_text, speaker_name, sprite, background, current_text_len):
        """
        Draw the complete scene with background, character sprite, and dialogue
        
        Args:
            scene_text: The full dialogue text
            speaker_name: Name of the speaking character
            sprite: Character sprite image (can be None)
            background: Background image (can be None)
            current_text_len: Number of characters to display (for typewriter effect)
        """
        # 1. Draw Background
        if background:
            # Scale background to fit screen if needed
            bg_scaled = pygame.transform.scale(background, self.screen.get_size())
            self.screen.blit(bg_scaled, (0, 0))
        else:
            # Fallback: black background
            self.screen.fill((0, 0, 0))
        
        # 2. Draw Character Sprite (Centered)
        if sprite:
            # Center horizontally, position vertically
            x = (self.screen.get_width() // 2) - (sprite.get_width() // 2)
            y = self.screen.get_height() - sprite.get_height() - 200  # Leave room for textbox
            self.screen.blit(sprite, (x, y))
        
        # 3. Draw Textbox
        textbox_x = 50
        textbox_y = self.screen.get_height() - 220
        self.screen.blit(self.textbox, (textbox_x, textbox_y))
        
        # 4. Draw Speaker Name
        name_surf = self.name_font.render(speaker_name, True, (255, 215, 0))  # Gold color
        self.screen.blit(name_surf, (textbox_x + 30, textbox_y + 10))
        
        # 5. Draw Typewriter Text with wrapping
        visible_text = scene_text[:current_text_len]
        
        # Wrap text to fit in textbox
        max_text_width = self.textbox.get_width() - 60  # Leave margins
        wrapped_lines = self.wrap_text(visible_text, self.font, max_text_width)
        
        # Draw each line
        line_y = textbox_y + 50
        line_height = 30
        
        for line in wrapped_lines[:4]:  # Show max 4 lines
            text_surf = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surf, (textbox_x + 30, line_y))
            line_y += line_height
        
        # 6. Draw "Click to continue" indicator if text is fully shown
        if current_text_len >= len(scene_text):
            indicator_font = pygame.font.SysFont("Arial", 18)
            indicator_text = "▼ Click to continue"
            indicator_surf = indicator_font.render(indicator_text, True, (0, 0 , 0))
            indicator_x = self.screen.get_width() - indicator_surf.get_width() - 70
            indicator_y = textbox_y + self.textbox.get_height() - 30
            
            # Blinking effect (simple)
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(indicator_surf, (indicator_x, indicator_y))
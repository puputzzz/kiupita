import pygame

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 24)
        self.name_font = pygame.font.SysFont("Arial", 30, bold=True)
        self.choice_font = pygame.font.SysFont("Arial", 28)  # NEW: Font for choices
        
        # ============================================================
        # SPRITE BOUNDARY BOX SETTINGS
        # ============================================================
        # Define the "box" that all character sprites must fit into
        # Sprites will be automatically resized to fit within these dimensions
        
        self.sprite_max_width = 500   # Maximum width in pixels
        self.sprite_max_height = 500  # Maximum height in pixels
        
        # Position of the sprite boundary box
        self.sprite_x_position = "center"  # "center", "left", "right", or a number (pixels from left)
        self.sprite_y_position = "bottom"  # "bottom", "center", "top", or a number (pixels from top)
        
        # Additional offset after fitting (fine-tuning)
        self.sprite_x_offset = 0      # Extra horizontal adjustment
        self.sprite_y_offset = 0      # Extra vertical adjustment
        
        # Maintain aspect ratio when resizing?
        self.maintain_aspect_ratio = True  # True = no stretching, False = stretch to fit exactly
        
        # ============================================================
        # CHOICE BUTTON SETTINGS
        # ============================================================
        self.choice_button_width = 880
        self.choice_button_height = 70
        self.choice_button_spacing = 15
        self.choice_button_start_y = 350  # Where the first choice appears on screen
        
        # Choice colors
        self.choice_normal_color = (50, 50, 80)
        self.choice_hover_color = (80, 120, 180)
        self.choice_border_color = (200, 200, 200)
        self.choice_text_color = (255, 255, 255)
        # ============================================================
        
        # UI Assets
        try:
            self.textbox = pygame.image.load("data/assets/ui/textbox.png").convert_alpha()
            print("✓ Textbox loaded successfully")
        except FileNotFoundError:
            print("⚠ Textbox not found, creating fallback")
            self.textbox = pygame.Surface((1180, 200))
            self.textbox.fill((50, 50, 50))
            self.textbox.set_alpha(220)
            pygame.draw.rect(self.textbox, (255, 255, 255), self.textbox.get_rect(), 3)
        
        # Debug mode - shows the sprite boundary box
        self.show_sprite_boundary = False  # Set to True to see the box
    
    def fit_sprite_to_boundary(self, sprite):
        """
        Resize sprite to fit within the defined boundary box
        Returns the resized sprite
        """
        original_width = sprite.get_width()
        original_height = sprite.get_height()
        
        if self.maintain_aspect_ratio:
            # Calculate scaling to fit within boundary while maintaining aspect ratio
            width_scale = self.sprite_max_width / original_width
            height_scale = self.sprite_max_height / original_height
            
            # Use the smaller scale to ensure sprite fits in both dimensions
            scale = min(width_scale, height_scale)
            
            # Only scale down, never scale up beyond original size
            # Remove this line if you want to scale up small sprites
            scale = min(scale, 1.0)
            
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
        else:
            # Stretch to fit exactly (not recommended, will distort)
            new_width = self.sprite_max_width
            new_height = self.sprite_max_height
        
        # Resize the sprite
        if new_width != original_width or new_height != original_height:
            resized_sprite = pygame.transform.smoothscale(sprite, (new_width, new_height))
            return resized_sprite
        else:
            return sprite
    
    def calculate_sprite_position(self, sprite):
        """
        Calculate where to draw the sprite based on position settings
        Returns (x, y) coordinates
        """
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        sprite_width = sprite.get_width()
        sprite_height = sprite.get_height()
        
        textbox_height = 220  # Space reserved for textbox at bottom
        
        # Calculate X position
        if self.sprite_x_position == "center":
            x = (screen_width - sprite_width) // 2
        elif self.sprite_x_position == "left":
            x = 50  # 50 pixels from left edge
        elif self.sprite_x_position == "right":
            x = screen_width - sprite_width - 50  # 50 pixels from right edge
        elif isinstance(self.sprite_x_position, (int, float)):
            x = int(self.sprite_x_position)
        else:
            x = (screen_width - sprite_width) // 2  # Default to center
        
        # Apply X offset
        x += self.sprite_x_offset
        
        # Calculate Y position
        available_height = screen_height - textbox_height
        
        if self.sprite_y_position == "bottom":
            y = screen_height - sprite_height - textbox_height
        elif self.sprite_y_position == "center":
            y = (available_height - sprite_height) // 2
        elif self.sprite_y_position == "top":
            y = 0
        elif isinstance(self.sprite_y_position, (int, float)):
            y = int(self.sprite_y_position)
        else:
            y = screen_height - sprite_height - textbox_height  # Default to bottom
        
        # Apply Y offset
        y += self.sprite_y_offset
        
        return (x, y)
    
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
        """
        # 1. Draw Background
        if background:
            bg_scaled = pygame.transform.scale(background, self.screen.get_size())
            self.screen.blit(bg_scaled, (0, 0))
        else:
            self.screen.fill((20, 20, 30))
        
        # 2. Draw Character Sprite with AUTO-FITTING
        if sprite:
            # Resize sprite to fit within boundary
            fitted_sprite = self.fit_sprite_to_boundary(sprite)
            
            # Calculate position
            sprite_x, sprite_y = self.calculate_sprite_position(fitted_sprite)
            
            # Draw the sprite
            self.screen.blit(fitted_sprite, (sprite_x, sprite_y))
            
            # DEBUG: Draw boundary box (if enabled)
            if self.show_sprite_boundary:
                screen_width = self.screen.get_width()
                screen_height = self.screen.get_height()
                textbox_height = 220
                
                # Calculate boundary box position
                if self.sprite_x_position == "center":
                    box_x = (screen_width - self.sprite_max_width) // 2
                elif self.sprite_x_position == "left":
                    box_x = 50
                elif self.sprite_x_position == "right":
                    box_x = screen_width - self.sprite_max_width - 50
                else:
                    box_x = (screen_width - self.sprite_max_width) // 2
                
                if self.sprite_y_position == "bottom":
                    box_y = screen_height - self.sprite_max_height - textbox_height
                elif self.sprite_y_position == "center":
                    available_height = screen_height - textbox_height
                    box_y = (available_height - self.sprite_max_height) // 2
                else:
                    box_y = 0
                
                # Draw red rectangle showing the boundary
                pygame.draw.rect(self.screen, (255, 0, 0), 
                               (box_x, box_y, self.sprite_max_width, self.sprite_max_height), 3)
        
        # 3. Calculate Textbox Position
        textbox_x = 50
        textbox_y = self.screen.get_height() - 220
        
        # Draw Textbox
        self.screen.blit(self.textbox, (textbox_x, textbox_y))
        
        # 4. Draw Speaker Name
        name_surf = self.name_font.render(speaker_name, True, (255, 200, 0))
        name_x = textbox_x + 30
        name_y = textbox_y + 15
        self.screen.blit(name_surf, (name_x, name_y))
        
        # 5. Draw Dialogue Text with wrapping
        visible_text = scene_text[:current_text_len]
        
        max_text_width = 1100
        wrapped_lines = self.wrap_text(visible_text, self.font, max_text_width)
        
        text_x = textbox_x + 30
        text_y = textbox_y + 60
        line_height = 32
        
        for i, line in enumerate(wrapped_lines[:4]):
            if line.strip():
                text_surf = self.font.render(line, True, (0, 0, 0))
                self.screen.blit(text_surf, (text_x, text_y + (i * line_height)))
        
        # 6. Draw "Click to continue" indicator
        if current_text_len >= len(scene_text):
            if pygame.time.get_ticks() % 1000 < 500:
                indicator_font = pygame.font.SysFont("Arial", 20)
                indicator_text = "▼ Click to continue"
                indicator_surf = indicator_font.render(indicator_text, True, (200, 200, 200))
                
                indicator_x = textbox_x + self.textbox.get_width() - indicator_surf.get_width() - 20
                indicator_y = textbox_y + self.textbox.get_height() - 35
                
                self.screen.blit(indicator_surf, (indicator_x, indicator_y))
    
    # ============================================================
    # NEW: CHOICE RENDERING METHODS
    # ============================================================
    
    def draw_choices(self, choices, hover_index=-1):
        """
        Draw choice buttons on the screen
        
        Args:
            choices: List of choice dictionaries with "text" key
            hover_index: Index of the currently hovered choice (-1 for none)
        """
        screen_width = self.screen.get_width()
        
        # Semi-transparent overlay to dim the background
        overlay = pygame.Surface((screen_width, self.screen.get_height()))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate starting position (centered horizontally)
        button_x = (screen_width - self.choice_button_width) // 2
        current_y = self.choice_button_start_y
        
        for i, choice in enumerate(choices):
            is_hovered = (i == hover_index)
            
            # Choose color based on hover state
            bg_color = self.choice_hover_color if is_hovered else self.choice_normal_color
            
            # Draw button background
            button_rect = pygame.Rect(
                button_x,
                current_y,
                self.choice_button_width,
                self.choice_button_height
            )
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=10)
            
            # Draw button border
            pygame.draw.rect(
                self.screen,
                self.choice_border_color,
                button_rect,
                3,
                border_radius=10
            )
            
            # Draw choice text (wrapped if needed)
            choice_text = choice.get("text", "")
            wrapped_text = self.wrap_text(choice_text, self.choice_font, self.choice_button_width - 40)
            
            # Calculate vertical centering for text
            total_text_height = len(wrapped_text) * 30
            text_start_y = current_y + (self.choice_button_height - total_text_height) // 2
            
            for line_idx, line in enumerate(wrapped_text):
                text_surf = self.choice_font.render(line, True, self.choice_text_color)
                text_rect = text_surf.get_rect(
                    centerx=button_x + self.choice_button_width // 2,
                    y=text_start_y + (line_idx * 30)
                )
                self.screen.blit(text_surf, text_rect)
            
            # Move to next button position
            current_y += self.choice_button_height + self.choice_button_spacing
    
    def get_choice_rects(self, num_choices):
        """
        Get the rectangles for all choice buttons
        Used for collision detection with mouse
        
        Args:
            num_choices: Number of choices to generate rects for
            
        Returns:
            List of pygame.Rect objects
        """
        screen_width = self.screen.get_width()
        button_x = (screen_width - self.choice_button_width) // 2
        current_y = self.choice_button_start_y
        
        rects = []
        for i in range(num_choices):
            rect = pygame.Rect(
                button_x,
                current_y,
                self.choice_button_width,
                self.choice_button_height
            )
            rects.append(rect)
            current_y += self.choice_button_height + self.choice_button_spacing
        
        return rects

# story.py
import pygame
from settings import *

class CutsceneManager:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(FONT_MONO, 24, bold=True)
        self.scenes = [] 
        self.current_index = 0
        self.timer = 0
        self.finished = False
        
        # Placeholder images if you don't have assets yet
        self.placeholder_img = pygame.Surface((WIDTH, 300))
        self.placeholder_img.fill(DARK_GREY)

    def start_sequence(self, sequence_data):
        """
        sequence_data = [
            {"text": "Line 1", "duration": 3.0, "color": WHITE, "bg": BLACK},
            ...
        ]
        """
        self.scenes = sequence_data
        self.current_index = 0
        self.timer = sequence_data[0]["duration"]
        self.finished = False

    def update(self, dt):
        if self.finished: return

        self.timer -= dt
        if self.timer <= 0:
            self.current_index += 1
            if self.current_index >= len(self.scenes):
                self.finished = True
            else:
                self.timer = self.scenes[self.current_index]["duration"]

    def draw(self):
        if self.finished: return
        
        data = self.scenes[self.current_index]
        
        # Draw Background
        bg_color = data.get("bg", BLACK)
        self.screen.fill(bg_color)
        
        # Draw Image (If you have paths, load them. For now, we use rects/text)
        # You can blit your specific cutscene images here based on index
        
        # Draw Text
        text_surf = self.font.render(data["text"], True, data.get("color", WHITE))
        rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text_surf, rect)

class DialogueSystem:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(FONT_MONO, 20)
        self.active = False
        self.text = ""
        self.choices = ["YES", "NO"]
        self.selected_index = 0
        self.on_confirm = None # Callback function

    def start_dialogue(self, text, callback_yes):
        self.active = True
        self.text = text
        self.on_confirm = callback_yes
        self.selected_index = 0

    def handle_input(self, event):
        if not self.active: return
        
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_a, pygame.K_LEFT]:
                self.selected_index = 0
            elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                self.selected_index = 1
            elif event.key == pygame.K_SPACE:
                if self.selected_index == 0: # YES
                    self.active = False
                    if self.on_confirm: self.on_confirm()
                else: # NO
                    # Loop effect: The text changes to refuse the player
                    self.text = "I have no choice... I must proceed."
                    self.selected_index = 0 # Force cursor to Yes

    def draw(self):
        if not self.active: return
        
        # Draw Box
        box_rect = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 150)
        pygame.draw.rect(self.screen, BLACK, box_rect)
        pygame.draw.rect(self.screen, WHITE, box_rect, 2)
        
        # Draw Main Text
        wrapped_text = self.text.split('\n')
        y_off = 0
        for line in wrapped_text:
            surf = self.font.render(line, True, WHITE)
            self.screen.blit(surf, (box_rect.x + 20, box_rect.y + 20 + y_off))
            y_off += 25
            
        # Draw Choices
        y_choice = box_rect.bottom - 40
        
        # YES
        col_yes = YELLOW if self.selected_index == 0 else GRAY
        yes_txt = self.font.render(f"> YES <" if self.selected_index == 0 else "  YES  ", True, col_yes)
        self.screen.blit(yes_txt, (box_rect.x + 100, y_choice))

        # NO
        col_no = YELLOW if self.selected_index == 1 else GRAY
        no_txt = self.font.render(f"> NO <" if self.selected_index == 1 else "  NO  ", True, col_no)
        self.screen.blit(no_txt, (box_rect.right - 200, y_choice))
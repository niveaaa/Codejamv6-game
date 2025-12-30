import pygame

# Screen
WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = 440

# Colors
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (200, 60, 60)
ORANGE = (200, 140, 60)
YELLOW = (240, 220, 120)
BLUE = (60, 120, 200)
GRAY = (90, 90, 90)
PURPLE = (160, 80, 200)
DARK_GREY = (40, 40, 40)
CRIMSON = (120, 0, 0)



# Fonts
# Using a system monospace font for that "hollow" feeling
FONT_MONO = "courier new" # or "consolas", "lucida console"

# Game State Keys
STATE_MENU = "menu"
STATE_CUTSCENE = "cutscene"    # NEW
STATE_DIALOGUE = "dialogue"    # NEW
STATE_GAME_PAPIA = "papia_fight"
STATE_GAME_HARUS = "harus_fight"
STATE_ENDING = "ending"
STATE_GAMEOVER = "gameover"

def load_strip(path, frame_count, frame_w=64, frame_h=64):
    try:
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        # If frame_w is None, calculate it based on total width
        if frame_w is None:
            frame_w = sheet.get_width() // frame_count
            frame_h = sheet.get_height()
            
        for i in range(frame_count):
            frame = sheet.subsurface((i * frame_w, 0, frame_w, frame_h))
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"ERROR loading {path}: {e}")
        # Return fallback surface
        s = pygame.Surface((frame_w or 64, frame_h or 64))
        s.fill((255, 0, 255))
        return [s]
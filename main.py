import pygame, sys, random
from settings import *
from player import Player
from bosses import PapiaBoss, HarusBoss, rect_point_distance
from story import CutsceneManager, DialogueSystem
from pygame.math import Vector2

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fading Memory")
clock = pygame.time.Clock()

# --- FONTS (Monospace for empty feeling) ---
try:
    font_ui = pygame.font.SysFont("courier new", 20, bold=True)
    font_big = pygame.font.SysFont("courier new", 48, bold=True)
except:
    font_ui = pygame.font.SysFont("arial", 20)
    font_big = pygame.font.SysFont("arial", 48)

# --- LOAD ASSETS ---
try:
    wife_portrait = pygame.image.load("assets/ui/wife_portrait.png").convert_alpha()
    wife_portrait = pygame.transform.scale(wife_portrait, (100, 100))
except:
    wife_portrait = pygame.Surface((100, 100))
    wife_portrait.fill((200, 150, 150))

# --- GAME VARIABLES ---
current_state = STATE_MENU
player = Player()
boss = None
memory_opacity = 255 
checkpoint_reached = False 

# Story Systems
cutscene_mgr = CutsceneManager(screen)
dialogue_sys = DialogueSystem(screen)

# Screen Shake
shake_timer = 0.0
shake_intensity = 0.0

def start_shake(intensity, duration=0.2):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

def draw_ui(screen, player, boss_name, boss_hp, boss_max):
    # Health Bar
    pygame.draw.rect(screen, RED, (20, 20, player.hp * 20, 20))
    pygame.draw.rect(screen, WHITE, (20, 20, player.max_hp * 20, 20), 2)
    
    # Boss Health Bar
    if boss_hp > 0:
        bar_w = 300
        ratio = boss_hp / boss_max
        pygame.draw.rect(screen, PURPLE, (WIDTH - 320, 20, bar_w * ratio, 20))
        pygame.draw.rect(screen, WHITE, (WIDTH - 320, 20, bar_w, 20), 2)
        txt = font_ui.render(boss_name, True, WHITE)
        screen.blit(txt, (WIDTH - 320, 45))

    # Wife Portrait (Fades based on memory_opacity)
    wife_portrait.set_alpha(memory_opacity)
    screen.blit(wife_portrait, (20, 60))
    
    # Dash UI
    if player.can_dash:
        col = BLUE if player.dash_cooldown <= 0 else GRAY
        pygame.draw.circle(screen, col, (40, 180), 10)
        txt = font_ui.render("DASH (K)", True, col)
        screen.blit(txt, (60, 170))

def draw_text_centered(text, y_offset=0, color=WHITE):
    surf = font_big.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    screen.blit(surf, rect)

# --- STORY TRANSITION FUNCTIONS ---

def start_intro_cutscene():
    global current_state
    current_state = STATE_CUTSCENE
    # Simple storyboard sequence
    cutscene_mgr.start_sequence([
        {"text": "We were happy.", "duration": 2.5, "bg": (220, 220, 240), "color": BLACK},
        {"text": "But then...", "duration": 1.5, "bg": (50, 50, 60), "color": WHITE},
        {"text": "I SAW HIM KILL HER.", "duration": 2.0, "bg": RED, "color": BLACK},
        {"text": "He ran into the caves.", "duration": 2.5, "bg": BLACK, "color": WHITE},
    ])

def finish_intro_cutscene():
    global current_state
    current_state = STATE_DIALOGUE
    dialogue_sys.start_dialogue(
        "To pursue the killer, you must be fast.\nThe memory of your FIRST DATE weighs you down.\n\nWill you sacrifice this memory to gain DASH?",
        unlock_dash_and_start
    )

def unlock_dash_and_start():
    global current_state, boss, memory_opacity
    player.can_dash = True
    memory_opacity = 180 # Fade portrait
    current_state = STATE_GAME_PAPIA
    boss = PapiaBoss()
    player.pos = Vector2(100, GROUND_Y)

def start_transition_dialogue():
    global current_state
    current_state = STATE_DIALOGUE
    dialogue_sys.start_dialogue(
        "One falls. But the killer (Harus) remains.\nYou are wounded and weak.\n\nSacrifice the memory of her VOICE to heal and continue?",
        unlock_checkpoint_and_start
    )

def unlock_checkpoint_and_start():
    global current_state, boss, memory_opacity, checkpoint_reached
    memory_opacity = 80 # Fade portrait more
    current_state = STATE_GAME_HARUS
    boss = HarusBoss()
    player.pos = Vector2(100, GROUND_Y)
    player.hp = player.max_hp # Heal
    checkpoint_reached = True

def start_ending_sequence():
    global current_state, memory_opacity
    current_state = STATE_ENDING
    memory_opacity = 0 # Gone

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Priority: Handle Dialogue Input first
        if current_state == STATE_DIALOGUE:
            dialogue_sys.handle_input(event)
            continue 

        if event.type == pygame.KEYDOWN:
            if current_state == STATE_MENU:
                if event.key == pygame.K_SPACE:
                    start_intro_cutscene()
                    
            elif current_state == STATE_ENDING:
                if event.key == pygame.K_SPACE:
                    # Restart Game
                    current_state = STATE_MENU
                    player = Player()
                    memory_opacity = 255
                    checkpoint_reached = False
                    
            elif current_state == STATE_GAMEOVER:
                if event.key == pygame.K_SPACE:
                    if checkpoint_reached:
                        # Retry Harus
                        start_transition_dialogue()
                        player = Player()
                        player.can_dash = True
                    else:
                        # Full Restart
                        current_state = STATE_MENU
                        player = Player()
                        memory_opacity = 255
                        checkpoint_reached = False

    # --- LOGIC UPDATES ---
    
    if current_state == STATE_CUTSCENE:
        cutscene_mgr.update(dt)
        if cutscene_mgr.finished:
            finish_intro_cutscene()

    elif current_state in [STATE_GAME_PAPIA, STATE_GAME_HARUS]:
        keys = pygame.key.get_pressed()
        player.update(dt, keys)
        
        if boss:
            boss.update(dt, player)
            
            # Check Boss Screen Shake Request
            if hasattr(boss, 'shake_requested') and boss.shake_requested > 0:
                start_shake(boss.shake_requested)
            
            # Player hits Boss
            if player.attack_state == "active" and player.attack_hitbox:
                if player.attack_hitbox.colliderect(boss.hurtbox()):
                    if not player.attack_damage_applied:
                        boss.hp -= 1
                        player.attack_damage_applied = True
                        if hasattr(boss, 'on_parried') and boss.parry_window:
                             boss.on_parried()

                # Player hits Orb (Papia)
                if isinstance(boss, PapiaBoss) and boss.orb:
                    orb_rect = pygame.Rect(boss.orb.pos.x - 20, boss.orb.pos.y - 20, 40, 40)
                    if player.attack_hitbox.colliderect(orb_rect):
                        boss.orb = None
                        boss.hp -= 1
                        player.attack_damage_applied = True

            # Boss hits Player
            boss_hit = False
            
            # 1. Generic Hitbox
            if hasattr(boss, 'attack_hitbox') and boss.attack_hitbox:
                if boss.attack_active and boss.attack_hitbox.colliderect(player.hurtbox()):
                    boss_hit = True
            
            # 2. Papia Projectiles
            if isinstance(boss, PapiaBoss):
                for m in boss.meteors:
                    if m.hits_player(player): boss_hit = True
                if boss.orb and (boss.orb.pos - player.pos).length() < 40:
                    boss_hit = True
                    boss.orb = None 

            # 3. Harus Shockwaves & Swing
            if isinstance(boss, HarusBoss):
                for s in boss.shockwaves:
                    if s.rect.colliderect(player.hurtbox()):
                        boss_hit = True
                        s.active = False 
                
                if boss.attack_type == "swing" and boss.attack_active:
                    tip = boss.axe_tip_pos()
                    if rect_point_distance(player.hurtbox(), tip) <= boss.swing_tip_radius:
                        boss_hit = True

            # Damage application
            if boss_hit and player.hit_recovery_timer <= 0:
                player.hp -= 1
                player.hit_recovery_timer = 1.0
                player.vel.x = -300 * player.facing
                start_shake(5, 0.2)

            # --- DEATH CHECKS ---
            if player.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                boss = None
                current_state = STATE_GAMEOVER
                
            elif boss.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                boss = None
                if current_state == STATE_GAME_PAPIA:
                    start_transition_dialogue()
                else:
                    start_ending_sequence()

    # --- DRAWING ---
    
    # Shake Calculation
    offset = (0, 0)
    if shake_timer > 0:
        shake_timer -= dt
        offset = (random.randint(-int(shake_intensity), int(shake_intensity)), 
                  random.randint(-int(shake_intensity), int(shake_intensity)))

    # Draw Background (Default Black)
    screen.fill(BLACK)
    
    if current_state == STATE_MENU:
        draw_text_centered("FADING MEMORY", -20)
        
        # Blink effect for "Press Start"
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            surf = font_ui.render("Press SPACE to Start", True, GRAY)
            screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))

    elif current_state == STATE_CUTSCENE:
        cutscene_mgr.draw()
        
    elif current_state == STATE_DIALOGUE:
        # Draw game background faintly behind dialogue
        pygame.draw.rect(screen, (10, 10, 15), (0, 0, WIDTH, HEIGHT))
        dialogue_sys.draw()

    elif current_state in [STATE_GAME_PAPIA, STATE_GAME_HARUS]:
        # Sky/Ground
        sky_col = (30, 30, 40) if current_state == STATE_GAME_PAPIA else (40, 10, 10)
        pygame.draw.rect(screen, sky_col, (0 + offset[0], 0 + offset[1], WIDTH, GROUND_Y))
        pygame.draw.rect(screen, (20, 20, 20), (0 + offset[0], GROUND_Y + offset[1], WIDTH, HEIGHT-GROUND_Y))
        
        player.draw(screen, offset)
        if boss: boss.draw(screen, offset)
        
        # UI
        boss_name = "PAPIA" if current_state == STATE_GAME_PAPIA else "HARUS (KILLER)"
        if boss: draw_ui(screen, player, boss_name, boss.hp, boss.max_hp)

    elif current_state == STATE_ENDING:
        draw_text_centered("IT IS DONE.", -40)
        draw_text_centered("I have my revenge...", 0)
        
        # Dramatic red text
        surf = font_ui.render("But I cannot remember her name.", True, RED)
        screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))
        
        draw_ui(screen, player, "", 0, 1) # Shows empty portrait

    elif current_state == STATE_GAMEOVER:
        draw_text_centered("YOU DIED", -20, RED)
        msg = "Press SPACE to Retry" if checkpoint_reached else "Press SPACE to Restart"
        surf = font_ui.render(msg, True, WHITE)
        screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

    pygame.display.flip()

pygame.quit()
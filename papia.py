# papia_patched.py
# Updated Papia boss: single big orb, odd/even meteor grid, smaller boss, repeatable AI.
import pygame, math, random
from pygame.math import Vector2

pygame.init()
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 18)

GROUND_Y = 440
FPS = 60

# Colors
WHITE = (240,240,240)
RED = (200,60,60)
BLUE = (60,120,200)
YELLOW = (240,220,120)
ORANGE = (200,140,60)
GRAY = (40,40,40)
BLACK = (10,10,10)
GREEN = (80,200,120)
PURPLE = (160,80,200)
CRIMSON = (180,40,60)

# -------- Helpers ----------
def rect_point_distance(rect: pygame.Rect, point: Vector2) -> float:
    dx = 0
    if point.x < rect.left:
        dx = rect.left - point.x
    elif point.x > rect.right:
        dx = point.x - rect.right
    dy = 0
    if point.y < rect.top:
        dy = rect.top - point.y
    elif point.y > rect.bottom:
        dy = point.y - rect.bottom
    return math.hypot(dx, dy)

# -------- Player (same + dash K) ----------
class Player:
    def __init__(self):
        self.pos = Vector2(220, GROUND_Y)
        self.vel = Vector2(0,0)
        self.facing = 1
        self.on_ground = True
        self.hp = 8

        self.attack_state = "ready"
        self.attack_timer = 0
        self.attack_hitbox = None
        self.attack_damage_applied = False

        self.hit_recovery_timer = 0

        # dash
        self.dash_cooldown = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.dash_speed = 700.0
        self.dash_time = 0.14
        self.dash_cooldown_time = 0.6
        self.invulnerable_during_dash = True

    def hurtbox(self):
        return pygame.Rect(self.pos.x-20, self.pos.y-80, 40, 80)

    def start_attack(self):
        if self.attack_state != "ready" or self.is_dashing:
            return
        self.attack_state = "windup"
        self.attack_timer = 0.10
        self.attack_hitbox = None
        self.attack_damage_applied = False

    def start_dash(self):
        if self.dash_cooldown > 0 or self.is_dashing or self.attack_state != "ready":
            return
        self.is_dashing = True
        self.dash_timer = self.dash_time
        self.dash_cooldown = self.dash_cooldown_time
        self.vel.x = self.dash_speed * self.facing
        if self.invulnerable_during_dash:
            self.hit_recovery_timer = self.dash_time

    def update(self, dt, keys):
        if self.hit_recovery_timer > 0:
            self.hit_recovery_timer -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        # gravity
        self.vel.y += 1300 * dt

        can_move = self.attack_state in ("ready", "recovery") and not self.is_dashing

        if can_move:
            if keys[pygame.K_a]:
                self.facing = -1
                self.vel.x = -200
            elif keys[pygame.K_d]:
                self.facing = 1
                self.vel.x = 200
            else:
                self.vel.x = 0

            # jump
            if keys[pygame.K_w] and self.on_ground:
                self.vel.y = -300
                self.jump_hold = 0.3
                self.on_ground = False

            if not keys[pygame.K_w]:
                self.jump_hold = 0

            if self.jump_hold > 0:
                self.vel.y -= 900 * dt
                self.jump_hold -= dt

            if keys[pygame.K_j] and self.attack_state == "ready":
                self.start_attack()
            if keys[pygame.K_k]:
                self.start_dash()
        else:
            if self.attack_state in ("windup","active"):
                self.vel.x = 0

        # dash logic
        if self.is_dashing:
            self.dash_timer -= dt
            if self.pos.x < 20 or self.pos.x > WIDTH-20:
                self.dash_timer = 0
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vel.x = 0

        # attack state machine
        if self.attack_state == "windup":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "active"
                self.attack_timer = 0.12
                offset = 48 * self.facing
                w, h = 56, 24
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox = pygame.Rect(x, self.pos.y - 60, w, h)
        elif self.attack_state == "active":
            if self.attack_hitbox:
                w = self.attack_hitbox.width
                offset = 48 * self.facing
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox.x = x
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "recovery"
                self.attack_timer = 0.20
                self.attack_hitbox = None
        elif self.attack_state == "recovery":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "ready"

        # clamp
        if abs(self.vel.x) > 400 and not self.is_dashing:
            self.vel.x = 400 * (1 if self.vel.x > 0 else -1)

        self.pos += self.vel * dt

        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            self.vel.y = 0
            self.on_ground = True

    def draw(self):
        color = BLUE
        if self.hit_recovery_timer > 0 and not self.is_dashing:
            if int(self.hit_recovery_timer*10) % 2 == 0:
                color = GREEN
        pygame.draw.rect(screen, color, self.hurtbox())
        if self.attack_hitbox:
            pygame.draw.rect(screen, YELLOW, self.attack_hitbox, 2)
        if self.is_dashing:
            for i in range(3):
                alpha = max(0, 200 - i*60)
                s = pygame.Surface((44,44), pygame.SRCALPHA)
                s.fill((120, 200, 255, alpha))
                screen.blit(s, (self.pos.x-22 - i*10*self.facing, self.pos.y-70))

# -------- Projectiles ----------
class Meteor:
    def __init__(self, x, delay=1.1):
        self.x = x
        self.y = -80
        self.target_y = GROUND_Y - 6
        self.radius = 26
        self.windup = delay
        self.fall_speed = 700.0
        self.active = False
        self.impact = False
        self.impact_timer = 0.0

    def update(self, dt):
        if self.impact:
            self.impact_timer -= dt
            return self.impact_timer > 0
        if self.windup > 0:
            self.windup -= dt
            if self.windup <= 0:
                self.active = True
            return True
        if self.active:
            self.y += self.fall_speed * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.impact = True
                self.impact_timer = 0.30
                self.active = False
            return True
        return True

    def draw(self):
        # telegraph on ground during windup
        if not self.active and not self.impact:
            t = max(0.0, min(1.0, 1.0 - self.windup / 1.0))
            r = int(self.radius + 10 * (0.8 + 0.2 * math.sin(pygame.time.get_ticks()/150)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            alpha = int(100 + 120 * t)
            pygame.draw.circle(surf, (220,90,40, alpha), (r, r), r, 3)
            screen.blit(surf, (self.x - r, GROUND_Y - r))
            inner = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(inner, (240,200,80, 90), (r,r), int(r*0.5))
            screen.blit(inner, (self.x-r, GROUND_Y - r))
        if self.active or self.impact:
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), 12)
            pygame.draw.line(screen, (220,150,60), (self.x-6, self.y-2), (self.x-30, self.y-18), 3)
        if self.impact:
            t = max(0.0, min(1.0, self.impact_timer / 0.30))
            r = int(self.radius * (1.2 + 1.4 * (1-t)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            a = int(180 * t)
            pygame.draw.circle(surf, (240,120,60,a), (r,r), r)
            screen.blit(surf, (self.x - r, GROUND_Y - r))

    def hits_player(self, player):
        if self.impact:
            center = Vector2(player.hurtbox().centerx, player.hurtbox().centery)
            d = math.hypot(center.x - self.x, center.y - GROUND_Y)
            return d <= (self.radius + 20)
        if self.active:
            tip = Vector2(self.x, self.y)
            d = rect_point_distance(player.hurtbox(), tip)
            return d <= 12
        return False

class LargeOrb:
    # Single large fast orb: short windup, launches toward player with high speed, short life
    def __init__(self, pos, target_player, speed=520.0, life=2.0):
        self.pos = Vector2(pos)
        self.target_player = target_player
        self.speed = speed
        self.life = life
        self.radius = 20
        self.windup = 0.45
        self.launched = False
        self.vel = Vector2(0,0)
        self.color = PURPLE

    def update(self, dt):
        if self.windup > 0:
            self.windup -= dt
            if self.windup <= 0:
                # lock-on and launch once
                dir = (self.target_player.pos - self.pos)
                if dir.length() == 0:
                    dir = Vector2(1,0)
                self.vel = dir.normalize() * self.speed
                self.launched = True
            return True
        if self.life <= 0:
            return False
        # once launched behave like a fast projectile with very minor seeking
        if self.launched:
            # tiny steering so it's fair
            to_player = (self.target_player.pos - self.pos)
            if to_player.length() > 0.1:
                desired = to_player.normalize() * self.speed
                self.vel = self.vel.lerp(desired, min(1.0, 2.0 * dt))
            self.pos += self.vel * dt
            # keep on-screen
            self.pos.x = max(0, min(WIDTH, self.pos.x))
            self.pos.y = max(-200, min(HEIGHT+200, self.pos.y))
            self.life -= dt
        return True

    def draw(self):
        if self.windup > 0:
            t = max(0.0, min(1.0, 1.0 - self.windup / 0.45))
            r = int(self.radius + 10 * (1.0 - t))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (140,80,200, int(130*t)), (r,r), r, 3)
            screen.blit(s, (int(self.pos.x-r), int(self.pos.y-r)))
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        g = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(g, (120,60,180,60), (self.radius*2, self.radius*2), self.radius*2)
        screen.blit(g, (int(self.pos.x - self.radius*2), int(self.pos.y - self.radius*2)))

    def hits_player(self, player):
        if not self.launched:
            return False
        center = Vector2(player.hurtbox().centerx, player.hurtbox().centery)
        d = center.distance_to(self.pos)
        return d <= (self.radius + 20)

# -------- Papia Boss (smaller, repeatable AI, odd/even grid) ----------
class PapiaBoss:
    def __init__(self):
        self.pos = Vector2(700, GROUND_Y)
        self.hp = 28
        self.half_hp = self.hp // 2
        # smaller hitbox
        self.half_width = 36
        self.hurt_height = 120

        self.state = "idle"
        self.state_timer = 0.0
        self.next_action_cooldown = 1.0
        self.meteors = []
        self.orb = None

        # meteor grid
        self.grid_positions = list(range(80, WIDTH-80, 40))  # columns across the ground
        self.meteor_count = 6
        self.meteor_delay_between = 0.14

        # orb tune
        self.orb_speed = 560.0
        self.orb_life = 1.7

        # phase: optional combo behavior after half HP
        self.use_phase_combo = True
        self.combo_enabled = False

        # telegraph
        self.is_casting = False
        self.cast_anim = 0.0
        self.current_parity = 0  # 0 even, 1 odd

        # ensure boss repeatedly attacks: small random initial delay
        self.next_action_cooldown = 0.8 + random.random()*0.6

    def hurtbox(self):
        return pygame.Rect(self.pos.x-self.half_width, self.pos.y-self.hurt_height, self.half_width*2, self.hurt_height)

    def update(self, dt, player):
        # update lists
        for m in self.meteors:
            m.update(dt)
        if self.orb:
            alive = self.orb.update(dt)
            if not alive:
                self.orb = None

        # remove finished meteors
        self.meteors = [m for m in self.meteors if not (m.impact and m.impact_timer <= 0)]

        # timers
        if self.next_action_cooldown > 0:
            self.next_action_cooldown -= dt
        if self.cast_anim > 0:
            self.cast_anim -= dt
            if self.cast_anim <= 0:
                self.is_casting = False

        # enable combo after half hp
        if self.use_phase_combo and not self.combo_enabled and self.hp <= self.half_hp:
            self.combo_enabled = True

        # decide next action when idle and ready
        can_pick = (self.next_action_cooldown <= 0) and (len(self.meteors) == 0) and (self.orb is None) and (not self.is_casting)
        if self.state == "idle" and can_pick:
            r = random.random()
            # if combo_enabled prefer combos sometimes
            combo_chance = 0.38 if self.combo_enabled else 0.0
            if r < combo_chance:
                self.start_combo(player)
            else:
                # choose between meteor heavy or single orb
                if random.random() < 0.65:
                    self.start_meteor_shower(player)
                else:
                    self.start_single_orb(player)

        # if we are casting_meteors/orb set the state back to idle once cast_anim ended
        if self.state != "idle" and not self.is_casting:
            self.state = "idle"

    # Meteor shower: choose a parity (odd or even) and spawn meteors only on that parity's columns
    def start_meteor_shower(self, player):
        self.state = "casting_meteors"
        self.is_casting = True
        self.cast_anim = 0.9
        self.next_action_cooldown = 1.0 + random.random()*0.6
        # choose parity randomly: 0 = even-index columns, 1 = odd-index columns
        self.current_parity = random.choice([0,1])
        # choose up to meteor_count columns from those parity positions
        parity_positions = [ (i,x) for i,x in enumerate(self.grid_positions) if (i % 2) == self.current_parity ]
        # bias towards player's column
        base_x = int(player.pos.x)
        # pick nearest N of parity_positions to player, but sprinkle randomness
        parity_positions.sort(key=lambda t: abs(t[1]-base_x))
        chosen = []
        available = [x for i,x in parity_positions]
        random.shuffle(available)
        # prefer picks near player: combine nearest and random
        near = sorted(parity_positions, key=lambda t: abs(t[1]-base_x))[:max(3, self.meteor_count)]
        picks = [x for i,x in near]
        # ensure uniqueness
        while len(chosen) < self.meteor_count and available:
            chosen.append(available.pop())
        # create meteors staggered
        for i,x in enumerate(chosen):
            m = Meteor(x, delay=0.9 + i*self.meteor_delay_between)
            self.meteors.append(m)

    def start_single_orb(self, player, delayed=0.0):
        # single big orb spawned near boss, short windup then launches quickly toward player
        self.state = "casting_orb"
        self.is_casting = True
        self.cast_anim = 0.55 + delayed
        self.next_action_cooldown = 1.0 + random.random()*0.5 + delayed
        spawn_x = self.pos.x + random.randint(-40, 40)
        spawn_y = self.pos.y - 120 + random.randint(-10,10)
        orb = LargeOrb(Vector2(spawn_x, spawn_y), player, speed=self.orb_speed, life=self.orb_life)
        orb.windup += delayed
        self.orb = orb

    def start_combo(self, player):
        # after half hp: do meteor shower then single orb after a little delay (more threatening)
        self.state = "casting_combo"
        self.is_casting = True
        self.cast_anim = 1.1
        self.next_action_cooldown = 1.6 + random.random()*0.6
        # first schedule meteors
        self.start_meteor_shower(player)
        # spawn single orb with slight extra delay so they "form together"
        self.start_single_orb(player, delayed=0.45)

    def draw(self):
        # smaller body
        rect = self.hurtbox()
        pygame.draw.rect(screen, CRIMSON, rect)
        # staff / casting
        if self.is_casting:
            t = max(0.0, min(1.0, self.cast_anim / 1.1))
            r = int(22 + 30*(t))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (200,100,200, 100), (r,r), r)
            screen.blit(s, (self.pos.x - r, self.pos.y - 220))
            pygame.draw.line(screen, PURPLE, (self.pos.x, self.pos.y-70), (self.pos.x, self.pos.y-200), 3)
        else:
            pygame.draw.line(screen, (120,40,140), (self.pos.x, self.pos.y-70), (self.pos.x, self.pos.y-140), 2)

        # draw meteors and orb
        for m in self.meteors:
            m.draw()
        if self.orb:
            self.orb.draw()

        # Draw big stripe/indicator showing active parity when meteors are present (telegraph)
        if any((not m.active and not m.impact) for m in self.meteors):
            # show text EVEN / ODD and highlight targeted columns
            label = "TARGET: EVEN" if self.current_parity == 0 else "TARGET: ODD"
            txt = FONT.render(label, True, WHITE)
            screen.blit(txt, (self.pos.x - txt.get_width()//2, self.pos.y - 260))
            # highlight targeted columns on ground
            for i,x in enumerate(self.grid_positions):
                if (i % 2) == self.current_parity:
                    surf = pygame.Surface((30,30), pygame.SRCALPHA)
                    # pulsing red ring
                    a = int(120 + 120 * (0.5 + 0.5*math.sin(pygame.time.get_ticks()/180 + i)))
                    pygame.draw.circle(surf, (220,70,40,a), (15,15), 12, 3)
                    screen.blit(surf, (x-15, GROUND_Y-15))

# -------- Main loop ----------
player = Player()
boss = PapiaBoss()
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.update(dt, keys)
    boss.update(dt, player)

    # Player attack hits orb and boss
    if player.attack_state == "active" and player.attack_hitbox:
        # destroy orb with attack (rewarding)
        if boss.orb:
            orb_rect = pygame.Rect(boss.orb.pos.x - boss.orb.radius, boss.orb.pos.y - boss.orb.radius,
                                   boss.orb.radius*2, boss.orb.radius*2)
            if player.attack_hitbox.colliderect(orb_rect):
                boss.orb = None
                boss.hp -= 1
                player.attack_damage_applied = True
        # hit boss
        if player.attack_hitbox.colliderect(boss.hurtbox()):
            if not player.attack_damage_applied:
                boss.hp -= 1
                player.attack_damage_applied = True

    # Meteor & orb damage to player
    for m in boss.meteors[:]:
        # meteor impact window
        if m.impact and m.impact_timer > 0:
            if m.hits_player(player):
                if player.hit_recovery_timer <= 0 and not player.is_dashing:
                    player.hp -= 2
                    player.hit_recovery_timer = 0.9
                    knock = -1 if player.pos.x > m.x else 1
                    player.vel.x = 280 * knock
            # impact_timer decremented inside update already
        # allow hitting falling meteor in mid-air
        if m.active and player.attack_state == "active" and player.attack_hitbox:
            tip = Vector2(m.x, m.y)
            if player.attack_hitbox.collidepoint(tip.x, tip.y):
                m.impact = True
                m.impact_timer = 0.18

    if boss.orb:
        if boss.orb.hits_player(player):
            if player.hit_recovery_timer <= 0 and not player.is_dashing:
                player.hp -= 1
                player.hit_recovery_timer = 0.8
                player.vel.x = -180 if boss.orb.pos.x > player.pos.x else 180
            boss.orb = None

    # Draw
    screen.fill(BLACK)
    pygame.draw.rect(screen, GRAY, (0,GROUND_Y,WIDTH,HEIGHT-GROUND_Y))
    player.draw()
    boss.draw()

    # HUD
    hud_lines = [
        f"Player HP: {player.hp}",
        f"Dash ready: {'YES' if player.dash_cooldown<=0 else 'NO'}",
        f"Boss HP: {boss.hp}",
        f"ComboPhase Enabled: {'YES' if boss.combo_enabled else 'NO'}",
        f"Meteors: {len(boss.meteors)}  Orb: {'YES' if boss.orb else 'NO'}",
    ]
    for i, line in enumerate(hud_lines):
        hud = FONT.render(line, True, WHITE)
        screen.blit(hud, (20, 20 + i*20))

    pygame.display.flip()

pygame.quit()

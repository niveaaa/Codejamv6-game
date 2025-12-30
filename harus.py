import pygame, math, random
from pygame.math import Vector2

def load_strip(path, frame_count, frame_w=64, frame_h=64):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(frame_count):
        frame = sheet.subsurface((i*frame_w, 0, frame_w, frame_h))
        frames.append(frame)
    return frames


pygame.init()
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 18)

GROUND_Y = 440
FPS = 60
BOSS_SCALE = 2.0


# Colors
WHITE = (240,240,240)
RED = (200,60,60)
BLUE = (60,120,200)
YELLOW = (240,220,120)
ORANGE = (200,140,60)
GRAY = (90,90,90)
BLACK = (10,10,10)
GREEN = (80,200,120)

# -------------------------------------
# Helpers
# -------------------------------------

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

def ease_in(t):
    return t * t

def ease_out(t):
    return 1 - (1 - t) * (1 - t)

# -------------------------------------
# Player
# -------------------------------------
class Player:
    def __init__(self):
        self.pos = Vector2(220, GROUND_Y)
        self.vel = Vector2(0,0)
        self.facing = 1
        self.on_ground = True
        self.hp = 6

        # attack states: ready -> windup -> active -> recovery
        self.attack_state = "ready"
        self.attack_timer = 0
        self.attack_hitbox = None
        self.attack_damage_applied = False
        self.cooldown = 0

        self.jump_hold = 0

        # when player gets hit, invulnerability timer
        self.hit_recovery_timer = 0

        # ---------------- Animation ----------------
        self.animations = {
            "idle": load_strip("assets/protag/idle.png", 4),
            "walk": load_strip("assets/protag/walk.png", 2),
            "windup": load_strip("assets/protag/windup.png", 2),
            "attack": load_strip("assets/protag/attack.png", 1),
            "recovery": load_strip("assets/protag/recovery.png", 1),
        }

        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0

        # animation speeds (seconds per frame)
        self.anim_speed = {
            "idle": 0.25,
            "walk": 0.15,
            "windup": 0.10,
            "attack": 0.20,
            "recovery": 0.20,
        }


    def hurtbox(self):
        return pygame.Rect(self.pos.x-20, self.pos.y-80, 40, 80)

    def attack_tip(self) -> Vector2:
        # tip is at the front edge of the player's attack hitbox
        if not self.attack_hitbox:
            return Vector2(self.pos.x, self.pos.y)
        if self.facing == 1:
            return Vector2(self.attack_hitbox.right, self.attack_hitbox.centery)
        else:
            return Vector2(self.attack_hitbox.left, self.attack_hitbox.centery)

    def start_attack(self):
        if self.attack_state != "ready":
            return
        self.attack_state = "windup"
        self.attack_timer = 0.10  # windup
        self.attack_hitbox = None
        self.attack_damage_applied = False
        self.cooldown = 0

    def update_animation(self, dt):
        # decide animation state
        if self.attack_state == "windup":
            state = "windup"
        elif self.attack_state == "active":
            state = "attack"
        elif self.attack_state == "recovery":
            state = "recovery"
        else:
            if not self.on_ground:
                state = "idle"
            elif abs(self.vel.x) > 10:
                state = "walk"
            else:
                state = "idle"

        # reset frame if animation changed
        if state != self.anim_state:
            self.anim_state = state
            self.anim_frame = 0
            self.anim_timer = 0

        # advance frames
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed[self.anim_state]:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % len(self.animations[self.anim_state])


    def update(self, dt, keys):
        # timers
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.hit_recovery_timer > 0:
            self.hit_recovery_timer -= dt

        # gravity
        self.vel.y += 1300 * dt

        # movement allowed only when not mid-attack windup/active
        can_move = self.attack_state in ("ready", "recovery")

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

            # attack input
            if keys[pygame.K_j] and self.attack_state == "ready":
                self.start_attack()
        else:
            # when windup/active disable horizontal movement but allow slight air control in recovery
            self.vel.x = 0 if self.attack_state in ("windup","active") else self.vel.x

        # attack state machine
        if self.attack_state == "windup":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                # go active
                self.attack_state = "active"
                # active window where damage can be applied; keep small but precise
                self.attack_timer = 0.12
                # create attack hitbox in front of player with reduced offset for precision
                offset = 48 * self.facing  # reduced reach so parry is harder
                w, h = 56, 24  # reduced size
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox = pygame.Rect(x, self.pos.y - 60, w, h)
                self.attack_damage_applied = False
        elif self.attack_state == "active":
            # follow player position during active window
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
                self.attack_damage_applied = False
                self.cooldown = 0.25
        elif self.attack_state == "recovery":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "ready"

        # physics
        # clamp horizontal velocity
        if abs(self.vel.x) > 400:
            self.vel.x = 400 * (1 if self.vel.x > 0 else -1)

        self.pos += self.vel * dt

        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            self.vel.y = 0
            self.on_ground = True

        self.update_animation(dt)


    def draw(self):
        frame = self.animations[self.anim_state][self.anim_frame]

        SCALE = 2.0  # <<< CHANGE THIS IF NEEDED

        # flip sprite if facing left
        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)

        # scale sprite
        frame = pygame.transform.scale(
            frame,
            (int(frame.get_width() * SCALE), int(frame.get_height() * SCALE))
        )

        # anchor sprite at feet
        draw_x = self.pos.x - frame.get_width() // 2
        draw_y = self.pos.y - frame.get_height()

        # hit recovery flash (debug-friendly)
        if self.hit_recovery_timer > 0:
            if int(self.hit_recovery_timer * 10) % 2 == 0:
                frame = frame.copy()
                frame.fill((120, 255, 180), special_flags=pygame.BLEND_ADD)

        screen.blit(frame, (draw_x, draw_y))

        # debug hitbox (optional)
        # pygame.draw.rect(screen, (0,255,0), self.hurtbox(), 1)
        if self.attack_hitbox:
            pygame.draw.rect(screen, (255,255,0), self.attack_hitbox, 2)



# -------------------------------------
# Shockwave
# -------------------------------------
class Shockwave:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y-40, 80, 60)
        self.speed = 380 * direction
        self.active = True

    def update(self, dt):
        self.rect.x += self.speed * dt
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.active = False

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect, 2)

# -------------------------------------
# Boss
# -------------------------------------
class AxeBoss:
    def __init__(self):
        self.pos = Vector2(700, GROUND_Y)
        self.hp = 18
        self.state = "idle"
        self.timer = 0
        # facing should not change mid-attack
        self.facing = -1

        self.half_width = 70
        self.attack_hitbox = None
        self.parry_window = False
        self.attack_active = False
        self.was_parried = False

        # swing/axe tip
        self.rotation = 0  # degrees
        self.attack_type = None
        self.stunned_timer = 0
        self.shockwaves = []

        # stored facing when attack started (locks direction)
        self.attack_facing = self.facing

        # swing params (adjustable)
        self.swing_reach = 160
        self.swing_tip_radius = 28
        self.swing_telegraph_time = 0.7
        self.swing_active_time = 0.25
        # track whether shockwave spawned on ground contact
        self._shockwave_spawned = False

        self.prev_tip_y = None


        # AI
        self.next_action_cooldown = 0

        # ---------------- Animation ----------------
        self.animations = {
            "idle": load_strip("assets/harus/idle.png", 4, 256, 256),
            "walk": load_strip("assets/harus/walk.png", 4, 256, 256),
            "windup": load_strip("assets/harus/windup.png", 4, 256, 256),
            "attack": load_strip("assets/harus/attack.png", 3, 256, 256),
            "recover": load_strip("assets/harus/recover.png", 4, 256, 256),
            "spin": load_strip("assets/harus/spin.png", 4, 256, 256),
        }

        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0.0

        self.anim_speed = {
            "idle": 0.25,
            "walk": 0.15,
            "windup": 0.12,
            "attack": 0.10,
            "recover": 0.18,
            "spin": 0.10,
        }


    def hurtbox(self):
        return pygame.Rect(self.pos.x-self.half_width, self.pos.y-180, self.half_width*2, 180)

    def axe_center(self) -> Vector2:
        return Vector2(self.pos.x, self.pos.y - 120)

    def axe_tip_pos(self) -> Vector2:
        center = self.axe_center()
        rad = math.radians(self.rotation)
        tip = Vector2(math.cos(rad)*self.swing_reach, math.sin(rad)*self.swing_reach)
        return center + tip
    
    def update_animation(self, dt, player):
        # Decide animation state from AI state
        if self.state == "telegraph":
            state = "spin" if self.attack_type == "spin" else "windup"
        elif self.state == "active":
            state = "spin" if self.attack_type == "spin" else "attack"
        elif self.state in ("recovery", "stunned"):
            state = "recover"
        else:
            if abs(player.pos.x - self.pos.x) > 300:
                state = "walk"
            else:
                state = "idle"

        # Reset animation on change
        if state != self.anim_state:
            self.anim_state = state
            self.anim_frame = 0
            self.anim_timer = 0.0

        # Advance frames
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed[self.anim_state]:
            self.anim_timer = 0
            self.anim_frame += 1
            if self.anim_frame >= len(self.animations[self.anim_state]):
                # attack animations should hold on last frame
                if self.anim_state in ("attack", "windup"):
                    self.anim_frame = len(self.animations[self.anim_state]) - 1
                else:
                    self.anim_frame = 0

    def update(self, dt, player):
        dist = abs(player.pos.x - self.pos.x)
        # only update facing when not mid-attack (so attack direction is locked)
        if self.state in ("idle", "recovery"):
            self.facing = 1 if player.pos.x > self.pos.x else -1

        # stunned
        if self.state == "stunned":
            self.stunned_timer -= dt
            if self.stunned_timer <= 0:
                # after stun go to recovery so boss isn't permanently stuck
                self.state = "recovery"
                self.timer = 0.7
            return

        # AI cooldown between actions
        if self.next_action_cooldown > 0:
            self.next_action_cooldown -= dt

        if self.state == "idle":
            # simple movement towards player if far
            if dist > 350:
                self.pos.x += (1 if player.pos.x > self.pos.x else -1) * 90 * dt
            else:
                # choose action when ready
                if self.next_action_cooldown <= 0:
                    # higher chance to swing when close
                    r = random.random()
                    if(dist < 160):
                        if r < 0.7:
                            self.start_spin()
                        else:
                            self.start_swing()
                    elif dist < 350:
                        if r < 0.2:
                            self.start_spin()
                        else:  
                            self.start_swing()
                    
                    else:
                        # short pause
                        self.next_action_cooldown = 0.6

        if self.state == "telegraph":
            # animate rotation during telegraph using ease-in so it accelerates toward impact
            self.timer -= dt
            if self.attack_type == "swing":
                # Axe stays fully behind boss during windup
                self.rotation = self.swing_start_angle
                self.parry_window = False
                self.attack_active = False
            else:
                # spin telegraph rotation
                self.rotation += 120 * dt
                self.parry_window = False

            if self.timer <= 0:
                self.state = "parry"
                # short parry window right before active
                self.timer = 0.12
                # lock facing for the attack
                self.attack_facing = self.facing
                # reset shockwave spawn flag
                self._shockwave_spawned = False

        elif self.state == "parry":
            self.timer -= dt
            if self.timer <= 0:
                self.start_active()

        elif self.state == "active":

            tip = self.axe_tip_pos()

            if self.prev_tip_y is not None:
                crossed_ground = (
                    self.prev_tip_y < GROUND_Y - 6 and
                    tip.y >= GROUND_Y - 6
                )
                if crossed_ground and not self._shockwave_spawned:
                        self.spawn_shockwave()
                        self._shockwave_spawned = True

            self.prev_tip_y = tip.y
            # in active we complete the arc and apply damage if tip touches the player
            # we will finish the rotation with an ease-out so motion slows after impact
            self.timer -= dt
            if self.attack_type == "swing":
                total = self.swing_active_time
                elapsed = total - self.timer
                t = max(0.0, min(1.0, elapsed / total))
                t_eased = ease_out(t)

                self.rotation = (
                    (1 - t_eased) * self.swing_start_angle +
                    t_eased * self.swing_target_angle
                )

                self.attack_active = True

            if self.timer <= 0:
                self.end_attack()

        elif self.state == "recovery":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "idle"
                self.was_parried = False
                self.parry_window = False
                self.attack_hitbox = None
                self.attack_active = False
                # small cooldown before next action
                self.next_action_cooldown = 0.4

        # update shockwaves
        for s in self.shockwaves:
            s.update(dt)
        self.shockwaves = [s for s in self.shockwaves if s.active]

        self.update_animation(dt, player)


    # -----------------------------
    def start_swing(self):
        
        # lock facing at the start of the move
        self.attack_facing = self.facing
        self.state = "telegraph"
        self.attack_type = "swing"
        self.swing_telegraph_time = 0.7
        self.swing_active_time = 0.25
        self.timer = self.swing_telegraph_time
        # more extreme angles to ensure arc travels from back/top to down
        self.swing_reach = 160
        self.swing_tip_radius = 28
        # set start and target angles explicitly per facing so direction is correct
        # Axe starts clearly behind the boss, ends down-forward
        if self.attack_facing == 1:
            self.swing_start_angle = -200
            self.swing_target_angle = 60
        else:
            self.swing_start_angle = 20
            self.swing_target_angle = -240

        self.rotation = self.swing_start_angle

        self.prev_tip_y = None
        self.was_parried = False
        self.parry_window = False
        self.attack_active = False
        self.attack_hitbox = None
        self._shockwave_spawned = False

    def start_spin(self):
        self.attack_facing = self.facing
        self.state = "telegraph"
        self.attack_type = "spin"
        # use similar windup feel but longer active
        self.swing_telegraph_time = 0.8
        self.sw_spin_active_time = 0.75
        self.timer = self.swing_telegraph_time
        self.rotation = 0
        self.was_parried = False
        self.parry_window = False
        # spin attack is larger area around boss; increase reach
        reach = 400   # reduced from 500
        height = 70
        x = self.pos.x - reach // 2
        self.attack_hitbox = pygame.Rect(x, self.pos.y - 90, reach, height)


    def start_active(self):
        self.state = "active"
        self.timer = self.swing_active_time if self.attack_type == "swing" else self.sw_spin_active_time
        self.attack_active = True
        self.parry_window = False

        # IMPORTANT: reset rotation to exact windup end
        if self.attack_type == "swing":
            self.rotation = self.swing_start_angle


    def end_attack(self):
        self.state = "recovery"
        self.timer = 1.0
        self.attack_active = False
        self.attack_hitbox = None

    def on_parried(self):
        # when parried, become stunned briefly then go to recovery
        self.was_parried = True
        self.state = "stunned"
        self.stunned_timer = 0.9
        self.attack_hitbox = None
        self.attack_active = False
        self.parry_window = False
        # slight knockback away from player
        self.pos.x -= self.attack_facing * 30

    def spawn_shockwave(self):
        # use locked facing at attack start
        self.shockwaves.append(
            Shockwave(self.pos.x+5 + self.attack_facing*120, self.pos.y, self.attack_facing)
        )

    def draw(self):
        frame = self.animations[self.anim_state][self.anim_frame]

        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)

        frame = pygame.transform.scale(
            frame,
            (int(frame.get_width() * BOSS_SCALE),
             int(frame.get_height() * BOSS_SCALE))
        )

        draw_x = self.pos.x - frame.get_width() // 2
        draw_y = self.pos.y - frame.get_height()

        screen.blit(frame, (draw_x, draw_y))


        # render telegraph/parry/active visuals
        if self.state in ("telegraph", "parry", "active"):
            color = ORANGE if self.state == "telegraph" else WHITE if self.state == "parry" else RED
            if self.attack_type == "swing":
                tip = self.axe_tip_pos()
                pygame.draw.circle(screen, color, (int(tip.x), int(tip.y)), self.swing_tip_radius, 2)
                center = self.axe_center()
                pygame.draw.line(screen, color, (center.x, center.y), (tip.x, tip.y), 4)
                # optionally draw arc path (debug) by sampling
                for i in range(0, 11):
                    a = (i/10.0)
                    ang = (1-a)*self.swing_start_angle + a*self.swing_target_angle
                    p = center + Vector2(math.cos(math.radians(ang))*self.swing_reach, math.sin(math.radians(ang))*self.swing_reach)
                    pygame.draw.circle(screen, (120,120,120), (int(p.x), int(p.y)), 2)
            else:
                length = 220
                angle = self.rotation
                end = Vector2(
                    self.pos.x + math.cos(math.radians(angle))*length,
                    self.pos.y - 120 + math.sin(math.radians(angle))*length
                )
                pygame.draw.line(screen, color, (self.pos.x, self.pos.y-120), end, 10)

        # draw rectangular hitbox for spin if present
        if self.attack_hitbox and self.attack_type == "spin":
            draw_color = ORANGE if self.parry_window else RED if self.attack_active else WHITE
            pygame.draw.rect(screen, draw_color, self.attack_hitbox, 2)

        for s in self.shockwaves:
            s.draw()

# -------------------------------------
player = Player()
boss = AxeBoss()
running = True

while running:
    dt = clock.tick(FPS) / 1000
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.update(dt, keys)
    boss.update(dt, player)

    # ------------------ Parry logic
    # Parry for swing: require player's attack active and boss in very short parry window
    if boss.attack_type == "swing" and boss.parry_window and player.attack_state == "active" and player.attack_hitbox:
        boss_tip = boss.axe_tip_pos()
        player_tip = player.attack_tip()
        if boss_tip.distance_to(player_tip) <= (boss.swing_tip_radius + 12):
            boss.on_parried()

    # For spin attacks we keep rectangle-based parry (if desired)
    if player.attack_state == "active" and player.attack_hitbox and boss.attack_hitbox and boss.parry_window:
        if player.attack_hitbox.colliderect(boss.attack_hitbox):
            boss.on_parried()

    # ------------------ Damage application
    # Boss swing: damage over whole trajectory once tip overlaps player's hurtbox while attack_active
    if boss.attack_type == "swing" and boss.attack_active:
        tip = boss.axe_tip_pos()
        d = rect_point_distance(player.hurtbox(), tip)
        if d <= boss.swing_tip_radius:
            if player.hit_recovery_timer <= 0:
                player.hp -= 2
                player.hit_recovery_timer = 0.9
                player.vel.x = -200 * boss.attack_facing
                # spawn shockwave immediately if tip hits ground
                if tip.y >= GROUND_Y - 6 and not boss._shockwave_spawned:
                    boss.spawn_shockwave()
                    boss._shockwave_spawned = True
                boss.end_attack()

    # Boss spin rectangle attack (longer active, bigger reach)
    if boss.attack_active and boss.attack_type == "spin" and boss.attack_hitbox and boss.attack_hitbox.colliderect(player.hurtbox()):
        if player.hit_recovery_timer <= 0:
            player.hp -= 2
            player.hit_recovery_timer = 0.9
            player.vel.x = -200 * boss.attack_facing
            boss.end_attack()

    # Shockwaves
    for s in boss.shockwaves:
        if s.rect.colliderect(player.hurtbox()):
            if player.hit_recovery_timer <= 0:
                player.hp -= 1
                player.hit_recovery_timer = 0.7
            s.active = False

    # Player attack damages boss only once per attack active window
    if player.attack_state == "active" and player.attack_hitbox and boss.hurtbox():
        if player.attack_hitbox.colliderect(boss.hurtbox()):
            if not player.attack_damage_applied:
                boss.hp -= 1
                player.attack_damage_applied = True

    # ------------------ Draw
    screen.fill(BLACK)
    pygame.draw.rect(screen, GRAY, (0,GROUND_Y,WIDTH,HEIGHT-GROUND_Y))
    player.draw()
    boss.draw()

    # HUD and debug info
    hud_lines = [
        f"Player HP: {player.hp}",
        f"Boss HP: {boss.hp}",
        f"Player State: {player.attack_state}",
        f"Player HitRecover: {player.hit_recovery_timer:.2f}",
        f"Boss State: {boss.state}",
        f"Boss ParryWindow: {boss.parry_window}",
        f"Boss Facing (locked): {boss.attack_facing if boss.state!='idle' else boss.facing}",
    ]
    for i, line in enumerate(hud_lines):
        hud = FONT.render(line, True, WHITE)
        screen.blit(hud, (20, 20 + i*20))

    pygame.display.flip()

pygame.quit()

import pgzrun
import random
import math
import os

WIDTH = 1152
HEIGHT = 672
FRAME_DELAY = 6

# center the whole screen
os.environ["SDL_VIDEO_CENTERED"] = "1"

# animation files (seperated one by one, please check folders inside the ./images folder)
TILES_IDLE = [f"wizard_idle/tile{i}" for i in range(1, 7)]
TILES_WALK = [f"wizard_walk/tile{i}" for i in range(1, 9)]
TILES_ATTACK = [f"wizard_attack/tile{i}" for i in range(1, 7)]
TILES_FIREBALL = [f"wizard_proj/tile{i}" for i in range(1, 5)]

SOUND_Z = "z"
SOUND_X = "x"
SOUND_C = "c"
SOUND_DEATH = "death"

class GameState:
    def __init__(self):
        self.game_started = False
        self.wizard_frame = 0
        self.frame_count = 0
        self.state = "idle"
        self.game_over = False
        self.spawn_timer = 0
        self.spawn_delay = 60
        self.score = 0
        self.health = 100
        self.power_up_timer = 0
        self.fireball_speed = 10
        self.combo = 0
        self.combo_timer = 0
        self.multi_shot_cooldown = 0
        self.single_shot_cooldown = 0
        
        self.wizard = Actor(TILES_IDLE[self.wizard_frame])
        self.wizard.pos = (50, HEIGHT - 108)
        
        self.fireballs = []
        self.characters = []
        self.enemy_fireballs = []

        self.shield_active = False
        self.shield_duration = 120
        self.shield_timer = 0
        self.shield_cooldown = 80
        self.shield_cooldown_timer = 0
        self.shield_radius = 40
        
        self.start_button = Rect((WIDTH / 2 - 120, HEIGHT / 2 + 80), (240, 70))
        self.button_hover = False
        self.title_offset = 0
        self.title_timer = 0

class Character:
    def __init__(self, enemy_type):
        self.enemy_type = enemy_type
        self.x = WIDTH
        self.y = HEIGHT - 108
        self.shoot_timer = random.randint(60, 120)
        
        enemy_configs = {
            "goblin": {"radius": 15, "speed": (3, 5), "health": 20},
            "ogre": {"radius": 30, "speed": (1, 2), "health": 50},
            "archer": {"radius": 20, "speed": (2, 3), "health": 30, "shoot_timer": (30, 60)},
            "boss": {"radius": 50, "speed": (1, 1), "health": 150, "shoot_timer": 30}
        }
        
        config = enemy_configs[enemy_type]
        self.radius = config["radius"]
        self.speed = random.uniform(*config["speed"])
        self.health = config["health"]
        if "shoot_timer" in config and enemy_type != "boss":
            self.shoot_timer = random.randint(*config["shoot_timer"])

class Fireball:
    def __init__(self, x, y, angle, speed):
        self.actor = Actor(TILES_FIREBALL[0])
        self.actor.pos = (x, y)
        self.angle = angle
        self.speed = speed
        self.frame = 0
        self.frame_count = 0

class EnemyFireball:
    def __init__(self, x, y, speed=8):
        self.x = x
        self.y = y
        self.radius = 10
        self.speed = speed

def draw():
    screen.clear()
    
    if not game.game_started:
        _draw_title_screen()
    else:
        _draw_game_screen()

def _draw_title_screen():
    for y in range(HEIGHT):
        r = 20 + (y * 80 // HEIGHT)
        g = 30 + (y * 100 // HEIGHT)
        b = 60 + (y * 120 // HEIGHT)
        screen.draw.line((0, y), (WIDTH, y), (r, g, b))

    # title with animation (css type of waving on screen)
    title_y = HEIGHT / 2 - 120 + math.sin(game.title_offset) * 10
    screen.draw.text(
        "Wizard Defense",
        center=(WIDTH / 2 + 3, title_y + 3),
        fontsize=80,
        color=(50, 50, 50)
    )
    screen.draw.text(
        "Wizard Defense",
        center=(WIDTH / 2, title_y),
        fontsize=80,
        color=(200, 150, 255)
    )

    # controls, list of how to play
    screen.draw.text(
        "Controls:",
        center=(WIDTH / 2 + 2, HEIGHT / 2 - 20 + 2),
        fontsize=40,
        color=(50, 50, 50)
    )
    screen.draw.text(
        "Controls:",
        center=(WIDTH / 2, HEIGHT / 2 - 20),
        fontsize=40,
        color=(180, 255, 180)
    )
    
    controls_text = "Left/Right: Move    X: Single Shot    Z: Multi-Shot    C: Shield"
    screen.draw.text(
        controls_text,
        center=(WIDTH / 2 + 2, HEIGHT / 2 + 20 + 2),
        fontsize=24,
        color=(50, 50, 50)
    )
    screen.draw.text(
        controls_text,
        center=(WIDTH / 2, HEIGHT / 2 + 20),
        fontsize=24,
        color=(255, 255, 200)
    )

    # start button (closes the screen and opens the game)
    button_color = (70, 130, 255) if not game.button_hover else (100, 160, 255)
    screen.draw.filled_rect(game.start_button, button_color)
    screen.draw.rect(game.start_button, (200, 200, 255))
    
    screen.draw.text(
        "Start Game",
        center=(WIDTH / 2 + 2, HEIGHT / 2 + 115 + 2),
        fontsize=48,
        color=(50, 50, 50)
    )
    screen.draw.text(
        "Start Game",
        center=(WIDTH / 2, HEIGHT / 2 + 115),
        fontsize=48,
        color=(255, 255, 255)
    )

def _draw_game_screen():
    screen.blit("background", (0, 0))
    screen.blit("platform", (0, 0))
    
    _draw_characters()
    _draw_enemy_fireballs()
    game.wizard.draw()
    _draw_wizard_fireballs()
    
    if game.shield_active:
        screen.draw.circle((game.wizard.x, game.wizard.y), game.shield_radius, (0, 191, 255))
    
    _draw_hud()

def _draw_characters():
    enemy_colors = {
        "goblin": (255, 0, 0),
        "ogre": (139, 69, 19),
        "archer": (0, 128, 0),
        "boss": (128, 0, 128)
    }
    
    for char in game.characters:
        color = enemy_colors[char.enemy_type]
        screen.draw.filled_circle((char.x, char.y), char.radius, color)
        screen.draw.text(
            f"{char.health}",
            center=(char.x, char.y - char.radius - 10),
            fontsize=20
        )

def _draw_enemy_fireballs():
    for fb in game.enemy_fireballs:
        screen.draw.filled_circle((fb.x, fb.y), fb.radius, (255, 165, 0))

def _draw_wizard_fireballs():
    for fireball in game.fireballs:
        fireball.actor.draw()

def _draw_hud():
    screen.draw.text(f"Score: {game.score}", topleft=(10, 10), fontsize=30)
    screen.draw.text(f"Health: {game.health}", topleft=(10, 40), fontsize=30)
    
    if game.power_up_timer > 0:
        screen.draw.text("Power Up!", topleft=(10, 70), fontsize=30, color="yellow")
    if game.combo > 1:
        screen.draw.text(f"Combo: {game.combo}x", topleft=(10, 100), fontsize=30, color="orange")
    if game.shield_cooldown_timer > 0:
        screen.draw.text(
            f"Shield CD: {game.shield_cooldown_timer // 60}",
            topleft=(10, 130),
            fontsize=30,
            color="cyan"
        )
    if game.multi_shot_cooldown > 0:
        screen.draw.text(
            f"Multi-Shot CD: {game.multi_shot_cooldown // 60}",
            topleft=(10, 160),
            fontsize=30,
            color="purple"
        )
    if game.single_shot_cooldown > 0:
        screen.draw.text(
            f"Shot CD: {game.single_shot_cooldown // 60}",
            topleft=(10, 190),
            fontsize=30,
            color="red"
        )
    
    if game.game_over:
        screen.draw.text(
            "GAME OVER",
            center=(WIDTH / 2, HEIGHT / 2),
            fontsize=60,
            color="red"
        )

def on_mouse_down(pos):
    if not game.game_started and game.start_button.collidepoint(pos):
        game.game_started = True

def on_mouse_move(pos):
    if not game.game_started:
        game.button_hover = game.start_button.collidepoint(pos)

def update_wizard_animation():
    game.frame_count += 1
    if game.frame_count >= FRAME_DELAY:
        game.frame_count = 0
        frames = {"idle": TILES_IDLE, "walk": TILES_WALK, "attack": TILES_ATTACK}[game.state]
        game.wizard_frame = (game.wizard_frame + 1) % len(frames)
        game.wizard.image = frames[game.wizard_frame]

def update_fireballs():
    for fireball in game.fireballs[:]:
        speed = fireball.speed * 2 if game.power_up_timer > 0 else fireball.speed
        fireball.actor.x += math.cos(fireball.angle) * speed
        fireball.actor.y -= math.sin(fireball.angle) * speed
        
        fireball.frame_count += 1
        if fireball.frame_count >= FRAME_DELAY:
            fireball.frame_count = 0
            fireball.frame = (fireball.frame + 1) % len(TILES_FIREBALL)
            fireball.actor.image = TILES_FIREBALL[fireball.frame]
        
        if (fireball.actor.x > WIDTH or fireball.actor.x < 0 or 
                fireball.actor.y < 0 or fireball.actor.y > HEIGHT):
            game.fireballs.remove(fireball)

def update_characters():
    _handle_spawning()
    _update_enemies()

def _handle_spawning():
    game.spawn_timer += 1
    if game.spawn_timer < game.spawn_delay:
        return
        
    game.spawn_timer = 0
    if game.score >= 100 and game.score % 100 == 0 and not any(c.enemy_type == "boss" for c in game.characters):
        game.characters.append(Character("boss"))
    else:
        enemy_type = random.choices(["goblin", "ogre", "archer"], weights=[0.5, 0.3, 0.2])[0]
        game.characters.append(Character(enemy_type))
    game.spawn_delay = max(30, 60 - game.score // 50)

def _update_enemies():
    for char in game.characters[:]:
        char.x -= char.speed
        _handle_enemy_shooting(char)
        _handle_fireball_collisions(char)
        _check_enemy_bounds(char)
    
    _update_enemy_fireballs()
    _update_timers()

def _handle_enemy_shooting(char):
    if char.enemy_type not in ["archer", "boss"]:
        return
        
    char.shoot_timer -= 1
    if char.shoot_timer > 0:
        return
        
    char.shoot_timer = random.randint(30, 60) if char.enemy_type == "archer" else 20
    speed = 10 if char.enemy_type == "boss" else 8
    game.enemy_fireballs.append(EnemyFireball(char.x, char.y, speed))

def _handle_fireball_collisions(char):
    for fireball in game.fireballs[:]:
        if (abs(fireball.actor.x - char.x) >= char.radius + 10 or 
                abs(fireball.actor.y - char.y) >= char.radius + 10):
            continue
            
        damage = 40 if game.power_up_timer > 0 else 20
        char.health -= damage
        game.fireballs.remove(fireball)
        if char.health <= 0:
            _handle_enemy_death(char)
            break

def _handle_enemy_death(char):
    game.characters.remove(char)
    score_value = 50 if char.enemy_type == "boss" else 10
    game.score += score_value
    game.combo += 1
    game.combo_timer = 180
    if random.random() < 0.15:
        game.power_up_timer = 300
    sounds.death.play()

def _check_enemy_bounds(char):
    if char.x < -char.radius:
        game.characters.remove(char)
        damage = 20 if char.enemy_type == "boss" else 5
        game.health -= damage

def _update_enemy_fireballs():
    for fb in game.enemy_fireballs[:]:
        fb.x -= fb.speed
        wizard_center = (game.wizard.x, game.wizard.y)
        distance = math.hypot(fb.x - wizard_center[0], fb.y - wizard_center[1])
        
        if game.shield_active and distance < game.shield_radius:
            game.enemy_fireballs.remove(fb)
        elif distance < 30:
            game.health -= 10
            game.enemy_fireballs.remove(fb)
            if game.health <= 0:
                game.game_over = True
        elif fb.x < 0:
            game.enemy_fireballs.remove(fb)

def _update_timers():
    if game.power_up_timer > 0:
        game.power_up_timer -= 1
    if game.combo_timer > 0:
        game.combo_timer -= 1
        if game.combo_timer == 0:
            game.score += game.combo * 5
            game.combo = 0
    if game.shield_active:
        game.shield_timer -= 1
        if game.shield_timer <= 0:
            game.shield_active = False
            game.shield_cooldown_timer = game.shield_cooldown
    if game.shield_cooldown_timer > 0:
        game.shield_cooldown_timer -= 1
    if game.multi_shot_cooldown > 0:
        game.multi_shot_cooldown -= 1
    if game.single_shot_cooldown > 0:
        game.single_shot_cooldown -= 1

def handle_input():
    if game.game_over:
        return
        
    if keyboard.right and game.wizard.x < WIDTH - 50:
        game.wizard.x += 5
        game.state = "walk"
    elif keyboard.left and game.wizard.x > 50:
        game.wizard.x -= 5
        game.state = "walk"
    elif keyboard.x and game.single_shot_cooldown == 0:
        game.state = "attack"
        fireball = Fireball(game.wizard.x + 40, game.wizard.y - 10, 0, game.fireball_speed)
        game.fireballs.append(fireball)
        game.single_shot_cooldown = 30
        sounds.x.play()
    elif keyboard.z and game.multi_shot_cooldown == 0:
        game.state = "attack"
        for i in range(-2, 3):
            angle = i * 0.2
            fireball = Fireball(game.wizard.x + 40, game.wizard.y - 10, angle, game.fireball_speed)
            game.fireballs.append(fireball)
        game.multi_shot_cooldown = 300
        sounds.z.play()
    elif keyboard.c and not game.shield_active and game.shield_cooldown_timer == 0:
        game.shield_active = True
        game.shield_timer = game.shield_duration
        sounds.c.play()

def update():
    if game.game_started and not game.game_over:
        handle_input()
        update_wizard_animation()
        update_fireballs()
        update_characters()
        
        if not (keyboard.right or keyboard.left or keyboard.x or keyboard.z):
            game.state = "idle"
    elif not game.game_started:
        game.title_timer += 1
        if game.title_timer >= 2:
            game.title_timer = 0
            game.title_offset += 0.1

game = GameState()
pgzrun.go()
#!/bin/python3

from dia_graphics import *
import time
import math

true = True
false = False

WIDTH = 1024
HEIGHT = 640

FPS = 30

# Setup Colors
COLORS = Enum()
COLORS.set(black = Color(0, 0, 0))
COLORS.set(white = Color(255, 255, 255))
COLORS.set(green = Color(0, 255, 0))
COLORS.set(grey_green = Color(31, 195, 63))
COLORS.set(dark_green = Color(0, 127, 0))
COLORS.set(brown = Color(63, 31, 0))
COLORS.set(light_brown = Color(127, 95, 31))
COLORS.set(light_grey = Color(200, 200, 200))
COLORS.set(light_blue = Color(150, 150, 255))
COLORS.set(light_red = Color(255, 127, 127))
COLORS.set(primary = Color(0, 200, 0, 127))
COLORS.set(secondary = Color(200, 0, 0, 127))
COLORS.set(consumable = Color(0, 0, 200, 127))
COLORS.set(red = Color(200, 0, 0))
COLORS.set(aqua = Color(100, 200, 200))

# Setup Message Translations
with open(get__path("rpg/data/translations/en.json"), "r") as file:
    MSG = eval(file.read())

# Initialize dia_graphics
init__logger("__LOGS__/rpg.log")
init__surface((WIDTH, HEIGHT), (WIDTH, HEIGHT), 8, 1.0, flags=false, title=MSG["title"], factor_default=HEIGHT, def_plugin="rpg", loading_sign_color=COLORS.light_brown, loading_bar_color=COLORS.dark_green, loading_bar_progress_color=COLORS.grey_green)
init__fonts(COLORS, MSG, name="rpg", scale_factor = 0.5)



# Class for a loaded Level
class Level:
    def __init__(self, lvl_id: str, init_dict: dict):
        self.lvl_id = lvl_id
        self.init_dict = init_dict
        
        with open(get__path(f"rpg/data/levels/{self.lvl_id}.json"), "r") as file:
            self.file_dict = eval(file.read())
        
        self.obstacle_hitboxes = [].copy()
        if "obstacle_hitboxes" in self.file_dict:
            for o in self.file_dict["obstacle_hitboxes"]:
                self.obstacle_hitboxes.append(ObstacleHitbox(o))
            
        self.interactable_objects = [].copy()
        if "interactable_objects" in self.file_dict:
            for i in self.file_dict["interactable_objects"]:
                self.interactable_objects.append(InteractableObject(i))
        
        self.movement_speed = self.file_dict["movement_speed"]
        self.starting_pos = self.file_dict["starting_pos"]
        self.start_dialog = MSG[self.file_dict["start_dialog"]]
        self.target = self.file_dict["target"]
        self.next_level = self.file_dict["next_level"]
        self.enemies = [].copy()
        if "enemies" in self.file_dict:
            for i in self.file_dict["enemies"]:
                self.enemies.append(Enemy(i))
        self.update_surface()
    
    def update_surface(self):
        self.surface = Image(f"levels/{self.lvl_id}-background.png")
    
    def get_size(self):
        return self.surface.size

    def get_background(self):
        return self.surface
    
    def delete_interactable_object(self, i):
        self.interactable_objects.pop(i)

    def __repr__(self):
        return f"Level({self.lvl_id}, {self.init_dict})"

    def __str__(self):
        return self.__repr__()


# Class for an ObstacleHitbox in a level
class ObstacleHitbox(Position):
    def __init__(self, init_dict: dict):
        self.init_dict = init_dict
        super().__init__(self.init_dict["start"], 
            (self.init_dict["end"][0] - self.init_dict["start"][0],
             self.init_dict["end"][1] - self.init_dict["start"][1]))
        self.type = self.init_dict["type"]

    def get_hitbox_surface(self):
        return Surface(self.size, Color(0, 255, 255, 63))

    def get_hitbox_screen_object(self, bg_pos):
        return ScreenObject(self.get_hitbox_surface()).set((bg_pos[0] + self.pos[0], bg_pos[1] + self.pos[1]))

    def __repr__(self):
        return f"Obstacle({self.init_dict})"

    def __str__(self):
        return self.__repr__()


# Class for an InteractableObject in a level
class InteractableObject(Position):
    def __init__(self, init_dict: dict):
        self.init_dict = init_dict
        self.type = self.init_dict["type"]
        self.pos = self.init_dict["pos"]
        self.image_file = self.init_dict["image"]
        self.image = Image(self.image_file)
        super().__init__(self.pos, self.image.size)
        self.layer = 4
        self.description = self.init_dict["description"]
        self.actions = self.init_dict["actions"]

    def get_surface(self):
        return self.image

    def get_screen_object(self):
        return ScreenObject(self.get_surface()).set_from_position(self)

    def get_hitbox_surface(self):
        return Surface(self.size, Color(255, 0, 255, 63))

    def get_hitbox_screen_object(self, bg_pos):
        return ScreenObject(self.get_hitbox_surface()).set((bg_pos[0] + self.pos[0], bg_pos[1] + self.pos[1]))
       
    def activate(self):
        global GLOBALS
        GLOBALS.in_action_menu = True
        GLOBALS.action_menu = self.get_action_menu()
        GLOBALS.active_interactable_id = GLOBALS.level.interactable_objects.index(self)
        load_dialog(MSG[self.description])
        GLOBALS.update_view = True
    
    def get_action_menu(self):
        return ActionMenu(self.actions, self.description)

    def __repr__(self):
        return f"Obstacle({self.init_dict})"

    def __str__(self):
        return self.__repr__()


# Class for an Item
class Item:
    def __init__(self, t: str, count: int = 1, slot: str = "secondary", data: dict = {}.copy()):
        self.type = t
        self.count = count
        self.slot = slot
        self.data = data.copy()
        self.surface = None
        self.update_surface()

    def update_surface(self):
        self.surface = Surface((96, 96))
        self.surface.blit(Image("items/" + self.type + ".png", (96, 96)), (0, 0))
        self.surface.blit(Text(MSG["item."+self.type], COLORS.light_grey), (48, 72), (True, False))
        if self.count > 1: self.surface.blit(Text(str(self.count), COLORS.light_grey, font_size=1.5), (4, 68), (False, False))
    
    def get_surface(self):
        return self.surface
        
    def __repr__(self):
        return f"Item('{self.type}', {self.count}, '{self.slot}', {self.data})"
    
    def __str__(self):
        return self.__repr__()


# Class for an ItemContainer, like a chest
class ItemContainer:
    def __init__(self, init_dict: dict = {"items": [].copy()}.copy()):
        self.init_dict = init_dict
        self.items = self.init_dict["items"]
        self.update_surface()

    def add_item(self, item: Item):
        self.items.append(item)
        return self

    def remove_item(self, item: Item):
        for i in self.items:
            if i.type == item.type:
                if i.count > item.count:
                    self.items.remove(i)
                    new = i.reduce(item.count)
                    self.items.append(new)
                    return True
                elif i.count == item.count:
                    self.items.remove(i)
                    return True
                else:
                    return False
    
    def update_surface(self):
        self.screen_object = ScreenObject(Surface((96 * 4, 96 * 4), Color(0, 0, 0, 127))).set((WIDTH // 2, HEIGHT // 5 * 2), 6, (True, True))
        for i in range(4):
            for j in range(4):
                self.screen_object.blit(Surface((90, 90), Color(0, 0, 0, 127)), (i*96+3, j*96+3))
        self.buttons = [].copy()
        for n, i in enumerate(self.items):
            o = Button(i.get_surface(), alt_text=f'{MSG["item."+i.type]} [{MSG["item_slot."+i.slot]}]').set_pos_pseudo_screen((n % 4 * 96, n // 4 * 96), self.screen_object)
            o.item = i
            self.buttons.append(o)
    
    def get_screen_object(self):
        return self.screen_object
    
    def __repr__(self):
        return "ItemContainer({'items': " + str(self.items) + "})"
    
    def __str__(self):
        return self.__repr__()


# Class for the player's Inventory
class Inventory(Enum):
    def __init__(self, init_dict: dict = {}.copy()):
        super().__init__()
        self.set_with_dict(init_dict)

    def __repr__(self):
        return f"Inventory({self.content})"

    def __str__(self):
        return self.__repr__()

    def initialize(self):
        self.content.clear()
        self.set(primary = None)
        self.set(secondary = None)
        self.set(consumable = None)
        return self
    
    def set_item(self, item: Item, slot: str = "primary"):
        if self.content[slot]:
            r = self.content[slot]
        else:
            r = None
        self.content[slot] = item
        return r
            

# Class for the Player
class Player:
    def __init__(self, init_level):
        self.pos = init_level.starting_pos
        self.screen_pos = [WIDTH // 2, HEIGHT // 2]
        self.update_surface()
    
    def update_surface(self):
        self.surfaces = {}.copy()
        self.surfaces["front"] = Image("player/player-front.png")
        self.surfaces["back"] = Image("player/player-back.png")
        self.surfaces["left"] = Image("player/player-left.png")
        self.surfaces["right"] = Image("player/player-right.png")
        self.facing = "front"
        self.surface = self.surfaces["front"]
        self.collision_size = (self.surface.size[0], 1)
    
    def get_surface(self):
        return self.surface
    
    def get_screen_object(self):
        return ScreenObject(self.get_surface()).set(self.screen_pos, 4, (True, True))
    
    def get_background_pos(self):
        return (WIDTH // 2 - self.pos[0] - self.surface.size[0] // 2, HEIGHT // 2 - self.pos[1] - self.surface.size[1] // 2)
    
    def get_screen_pos(self):
        return self.screen_pos
    
    def move(self, movement: tuple = (0, 0)):
        for o in GLOBALS.level.obstacle_hitboxes:
            if o.get_collision(Position((self.pos[0] + movement[0], self.pos[1] + self.surface.size[1] + movement[1]), self.collision_size)):
                return
        for o in GLOBALS.level.interactable_objects:
            if o.get_collision(Position((self.pos[0] + movement[0], self.pos[1] + self.surface.size[1] + movement[1]), self.collision_size)):
                o.activate()
                return
        old_pos = self.pos
        self.pos = (self.pos[0] + movement[0], self.pos[1] + movement[1])   
          
        # Check if the player reached the level border (target)
        if GLOBALS.level.target == "{border}":
            if GLOBALS.player.collides_edge():
                self.pos = old_pos
                advance_level()
                
        if movement[0] > 0:
            self.facing = "right"
            self.surface = self.surfaces["right"]
        elif movement[0] < 0:
            self.facing = "left"
            self.surface = self.surfaces["left"]
        elif movement[1] < 0:
            self.facing = "back"
            self.surface = self.surfaces["back"]
        else:
            self.facing = "front"
            self.surface = self.surfaces["front"]
        close_action_menu()
        close_container()
    
    def collect_item(self, item: Item):
        return SAVESTATE.inventory.set_item(item, item.slot)
    
    def collides_edge(self):
        if self.pos[0] // 2 < 0 or self.pos[0] + self.surface.size[0] > GLOBALS.level.get_size()[0]:
            return True
        if self.pos[1] // 2 < 0 or self.pos[1] + self.surface.size[1] > GLOBALS.level.get_size()[1]:
            return True
    
    def damage(self, hp):
        if SAVESTATE.hp > hp:
            SAVESTATE.hp -= hp
        else:
            SAVESTATE.hp = 0
            game_over()
            
    def heal(self, hp):
        if SAVESTATE.hp + hp > 100:
            SAVESTATE.hp = 100
        else:
            SAVESTATE.hp += hp


# Class for an ActionMenu when activating an InteractableObject
class ActionMenu:
    def __init__(self, contents: list, description: str):
        self.contents = contents
        self.description = description
        self.update_surface()

    def update_surface(self):
        self.screen_object = ScreenObject(Surface((400, 70*len(self.contents)), Color(0, 0, 0, 0))).set((WIDTH // 2, HEIGHT // 7 * 6), 6, (True, False))
        self.buttons = [].copy()
        for n, i in enumerate(self.contents):
            o = Button(Surface((400, 70), Color(0, 0, 0, 127)), Surface((400, 70), COLORS.dark_green)).set_pos_pseudo_screen((0, n*70), self.screen_object)
            o.blit_all(Text(MSG[i["name"]], COLORS.light_grey, font_size=2), (200, 35), (True, True))
            o.content = i
            self.buttons.append(o)

    def get_screen_object(self):
        return self.screen_object


# Class for Enemies to fight
class Enemy:
    def __init__(self, init_dict: dict):
        self.init_dict = init_dict.copy()
        self.pos = self.init_dict["start_pos"]
        self.orig_pos = self.pos.copy()
        self.trigger = self.init_dict["trigger"]
        self.pursuit = self.init_dict["pursuit"]
        self.attack = self.init_dict["attack"]
        self.speed = self.init_dict["speed"]
        self.hp = self.init_dict["hp"]
        self.drops = self.init_dict["drops"].copy() if "drops" in self.init_dict else [].copy()
        self.move_timeout = self.init_dict["move_timeout"]
        self.current_move_timeout = self.move_timeout
        self.triggered = False
        self.attacking = False
        self.attack_animation_frame = 0
        self.current_attack_timeout = 0
        self.update_surface()
    
    def update_surface(self):
        self.surface = Image(self.init_dict["image"])
        
    def get_screen_object(self):
        return ScreenObject(self.surface).set(self.pos, 4)
    
    def check_trigger(self):
        return eval(self.trigger)
    
    def calculate_move(self):
        start = (self.pos[0] + self.surface.size[0] // 2, self.pos[1] + self.surface.size[1] // 2)
        target = (GLOBALS.player.pos[0] + GLOBALS.player.surface.size[0] // 2, GLOBALS.player.pos[1] + GLOBALS.player.surface.size[1] // 2)
        dx = target[0] - start[0]
        dy = target[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist > 100:
            move_x = min(self.speed, dist) * dx / dist
            move_y = min(self.speed, dist) * dy / dist
            self.move((move_x, move_y))
        else:
            self.start_attack()
        self.current_move_timeout = self.move_timeout
    
    def start_attack(self):
        if not self.attacking and self.attack_animation_frame == 0 and self.current_attack_timeout <= 0:
            self.current_attack_timeout = self.attack["timeout"]
            if self.attack["type"] == "jump":
                self.attacking = True
                self.attack_orig = self.pos.copy()
                self.attack_target = GLOBALS.player.pos
            
    def animate_jump_attack(self, frame):
        dx = self.attack_target[0] - self.attack_orig[0]
        dy = self.attack_target[1] - self.attack_orig[1]
        dist = math.hypot(dx, dy)
        move_x = min(dist / self.attack["frames"] * frame, dist) * dx / dist
        move_y = min(dist / self.attack["frames"] * frame, dist) * dy / dist
        self.pos = [self.attack_orig[0] + move_x, self.attack_orig[1] + move_y]
    
    def update_attack_animation(self):
        if self.current_attack_timeout > 0: self.current_attack_timeout -= 1
        if self.attacking:
            if self.attack["type"] == "jump":
                self.attack_animation_frame += 1
                self.animate_jump_attack(self.attack_animation_frame)
                GLOBALS.update_view = True
                if self.attack_animation_frame >= self.attack["frames"]:
                    self.attack_player()
        else:
            if self.attack["type"] == "jump":
                if self.attack_animation_frame > 0:
                    self.attack_animation_frame -= 1
                    self.animate_jump_attack(self.attack_animation_frame)
                    GLOBALS.update_view = True
    
    def attack_player(self):
        GLOBALS.player.damage(self.attack["damage"])
        self.attacking = False
    
    def move(self, movement: tuple = (0, 0)):
        self.pos[0] += movement[0]
        self.pos[1] += movement[1]
        
    def damage(self, hp):
        if self.hp > hp:
            self.hp -= hp
            return False
        else:
            self.hp = 0
            return True
    
    def __repr__(self):
        return f"Enemy({self.init_dict})"
    
    def __str__(self):
        return self.__repr__()



# Setup Screen Objects in Menu
def setup_menu():
    screen_objects = Enum()

    screen_objects.set(title = ScreenObject(
                Text(MSG["title"], COLORS.grey_green, font_size = 6))
            .set((WIDTH // 2, HEIGHT // 4), 6, (True, True)))

    screen_objects.set(play = Button(
                Text(MSG["menu.play"], COLORS.grey_green, font_size = 3),
                Text(MSG["menu.play"], COLORS.dark_green, font_size = 3))
            .set((WIDTH // 4, HEIGHT // 8 * 4), 5, (False, True)))

    screen_objects.set(settings = Button(
                Text(MSG["menu.settings"], COLORS.grey_green, font_size = 3),
                Text(MSG["menu.settings"], COLORS.dark_green, font_size = 3))
            .set((WIDTH // 4, HEIGHT // 8 * 5), 5, (False, True)))

    screen_objects.set(quit = Button(
                Text(MSG["menu.quit"], COLORS.grey_green, font_size = 2),
                Text(MSG["menu.quit"], COLORS.dark_green, font_size = 2))
            .set((WIDTH // 8, HEIGHT // 8 * 7), 5, (False, True)))

    return screen_objects

# Setup Screen Objects in Level Select
def setup_level_select():
    screen_objects = Enum()

    screen_objects.set(title = ScreenObject(
                Text(MSG["title"], COLORS.grey_green, font_size = 6))
            .set((WIDTH // 2, HEIGHT // 4), 6, (True, True)))

    screen_objects.set(subtitle = ScreenObject(
                Text(MSG["menu.level_select"], COLORS.grey_green, font_size = 3))
            .set((WIDTH // 8 * 1, HEIGHT // 5 * 2), 6, (False, True)))

    screen_objects.set(cont = Button(
                Text(f'{MSG["menu.continue"]} ({MSG["menu.level"]} {SAVESTATE.level_id})', COLORS.grey_green, font_size = 3),
                Text(f'{MSG["menu.continue"]} ({MSG["menu.level"]} {SAVESTATE.level_id})', COLORS.dark_green, font_size = 3))
            .set((WIDTH // 8 * 2, HEIGHT // 8 * 4), 5, (False, True)))

    screen_objects.set(restart = Button(
                Text(MSG["menu.restart"], COLORS.grey_green, font_size = 3),
                Text(MSG["menu.restart"], COLORS.dark_green, font_size = 3))
            .set((WIDTH // 8 * 2, HEIGHT // 8 * 5), 5, (False, True)))

    screen_objects.set(back = Button(
                Text(MSG["menu.back"], COLORS.grey_green, font_size = 2),
                Text(MSG["menu.back"], COLORS.dark_green, font_size = 2))
            .set((WIDTH // 8, HEIGHT // 8 * 7), 5, (False, True)))

    return screen_objects

# Setup (Screen) Objects for a Level
def setup_level(lvl_id: str):
    screen_objects = Enum()
    
    draw__loading__sign__page("loading.level", 0.5)

    level = Level(lvl_id, {})
    
    player = Player(level)

    screen_objects.set(background = ScreenObject(level.get_background()).set((0, 0), 1))
    
    screen_objects.set(obstacle_hitboxes = [].copy())
    for o in level.obstacle_hitboxes:
        screen_objects.obstacle_hitboxes.append(o)
        
    screen_objects.set(interactable_objects = [].copy())
    for o in level.interactable_objects:
        screen_objects.interactable_objects.append(o)
    
    save_savestate(SAVESTATE)
    
    load_dialog(level.start_dialog)

    return screen_objects, level, player

# Setup Screen Objects in Pause Menu
def setup_pause_menu():
    screen_objects = Enum()
    
    screen_objects.set(overlay = ScreenObject(Surface((WIDTH, HEIGHT), COLORS.black.copy().set_alpha(127))).set((0, 0), 6))
    screen_objects.set(title = ScreenObject(Text(MSG["pause"], COLORS.grey_green, font_size = 3)).set((WIDTH // 2, HEIGHT // 4), 7, (True, True)))
    
    screen_objects.set(cont = Button(
                Text(MSG["pause.continue"], COLORS.grey_green, font_size = 2),
                Text(MSG["pause.continue"], COLORS.dark_green, font_size = 2))
            .set((WIDTH // 4, HEIGHT // 8 * 4), 7, (False, True)))
            
    screen_objects.set(quit = Button(
                Text(MSG["pause.quit"], COLORS.grey_green, font_size = 2),
                Text(MSG["pause.quit"], COLORS.dark_green, font_size = 2))
            .set((WIDTH // 8, HEIGHT // 8 * 7), 7, (False, True)))
    
    return screen_objects

# Setup Screen Objects in End Credits
def setup_credits():
    GLOBALS.in_level = False
    GLOBALS.in_credits = True
    
    pages = [].copy()
    
    with open(get__path("rpg/data/levels/credits.json"), "r") as file:
        json = eval(file.read())
    
    for p in json["pages"]:
        page = [].copy()
        amount = len(p)+1
        for n, i in enumerate(p):
            page.append(ScreenObject(Text(MSG[i["text"]], i["color"], font_size = i["size"])).set((WIDTH // 2, HEIGHT // amount * (n+1)), 5, (True, True)))
        pages.append(page)
    
    return pages

# Save SAVESTATE to File
def save_savestate(savestate: Enum, filename: str = "savestate.json"):
    with open(filename, "w") as file:
        file.write(str(savestate))

# Load SAVESTATE from File
def load_savestate(default: Enum = None, filename: str = "savestate.json"):
    try:
        with open(filename, "r") as file:
            return Enum().set_with_dict(eval(file.read()))
    except:
        return default

# Activate ActinMenu button
def activate_action(content: dict):
    global GLOBALS
    if content["type"] == "del":
        if "required" in content:
            for k, i in content["required"].items():
                if not SAVESTATE.inventory.content[k] or SAVESTATE.inventory.content[k].type != i:
                    load_dialog(MSG[content["required_dialog"]])
                    break
            else:
                GLOBALS.level.delete_interactable_object(GLOBALS.active_interactable_id)
        else:
            GLOBALS.level.delete_interactable_object(GLOBALS.active_interactable_id)
    elif content["type"] == "transform":
        if "required" in content:
            for k, i in content["required"].items():
                if not SAVESTATE.inventory.content[k] or SAVESTATE.inventory.content[k].type != i:
                    load_dialog(MSG[content["required_dialog"]])
                    break
            else:
                GLOBALS.level.interactable_objects[GLOBALS.active_interactable_id] = InteractableObject(content["transform"])
        else:
            GLOBALS.level.interactable_objects[GLOBALS.active_interactable_id] = InteractableObject(content["transform"])
    elif content["type"] == "advance":
        if "required" in content:
            for k, i in content["required"].items():
                if not SAVESTATE.inventory.content[k] or SAVESTATE.inventory.content[k].type != i:
                    load_dialog(MSG[content["required_dialog"]])
                    break
            else:
                advance_level()
        else:
            advance_level()
    elif content["type"] == "ItemContainer":
        GLOBALS.open_container = content["constructor"]
        GLOBALS.in_container = True
    close_action_menu()

# Close the current ActionMenu
def close_action_menu():
    GLOBALS.in_action_menu = False
    GLOBALS.action_menu = None
    GLOBALS.active_interactable_id = None
    GLOBALS.update_view = True

# Close the current Container
def close_container():
    GLOBALS.in_container = False
    GLOBALS.open_container = None
    GLOBALS.update_view = True

# Draw the player's Inventory
def draw_inventory():
    for n, i in {0: "primary", 1: "secondary", 2: "consumable"}.items():
        o = ScreenObject(Surface((96, 96), Color(0, 0, 0, 127))).set((68, 120 * n + 20), 6, (True, False))
        o.blit(Surface((90, 90), COLORS.content[i]), (3, 3))
        if SAVESTATE.inventory.content[i]:
            o.blit(SAVESTATE.inventory.content[i].get_surface(), (0, 0))
        draw(o)
        t = ScreenObject(Text(MSG["item_slot."+i], COLORS.light_grey, Color(0, 0, 0, 127), 1)).set((68, 120 * n + 100 + 20), 6, (True, False))
        draw(t)

# Draw the player's health points
def draw_hp():
    if SAVESTATE.hp > 30:
        c = COLORS.light_blue
    else:
        c = COLORS.light_red
    so = ScreenObject(Text(f"HP: {SAVESTATE.hp} / 100", c, Color(0, 0, 0, 127), 2)).set((WIDTH // 2, 16), 6, (True, False))
    draw(so)
    for n, e in enumerate(GLOBALS.level.enemies):
        if e.triggered:
            so = ScreenObject(Text(f"Enemy HP: {e.hp}", COLORS.red, Color(0, 0, 0, 127), 2)).set((WIDTH // 2, 16 + 34 * (n+1)), 6, (True, False))
            draw(so)

# Load a new dialog
def load_dialog(dialog_list: list = [].copy()):
    GLOBALS.dialog = dialog_list.copy()
    GLOBALS.dialog_id = 0 if dialog_list else -1
    GLOBALS.dialog_animation_frame = 0 if dialog_list else -1

# Advance in the current dialog
def advance_dialog(amount: int = 1):
    GLOBALS.dialog_id += 1
    GLOBALS.dialog_animation_frame = 0
    if GLOBALS.dialog_id >= len(GLOBALS.dialog):
        GLOBALS.dialog_id = -1
        GLOBALS.dialog = [].copy()
        GLOBALS.dialog_animation_frame = -1

# Draw the current dialog
def draw_dialog():
    if GLOBALS.dialog_id >= 0:
        so = ScreenObject(Surface((WIDTH - 16, HEIGHT // 4 - 16), Color(0, 0, 0, 127))).set((8, HEIGHT // 4 * 3 + 8), 6)
        length = len(GLOBALS.dialog[GLOBALS.dialog_id][:GLOBALS.dialog_animation_frame])
        max_chars = 55
        for n in range(length // max_chars + 1):
            if (n+1) * max_chars <= length: t = GLOBALS.dialog[GLOBALS.dialog_id][n*max_chars:(n+1)*max_chars]
            else: t = GLOBALS.dialog[GLOBALS.dialog_id][n*max_chars:length]
            so.blit(Text(t, COLORS.light_grey, font_size=2), (WIDTH // 2 - 8, 16+32*n), (True, False))
        draw(so)

# Draw debugging hitboxes
def draw_hitboxes(screen_objects):
    if GLOBALS.dev:
        for o in screen_objects.obstacle_hitboxes:
            draw(o.get_hitbox_screen_object(GLOBALS.player.get_background_pos()))
        for o in screen_objects.interactable_objects:
            draw(o.get_hitbox_screen_object(GLOBALS.player.get_background_pos()))

# Use item in CONSUMABLE slot
def use_consumable():
    if SAVESTATE.inventory.consumable:
        if "healing" in SAVESTATE.inventory.consumable.data:
            GLOBALS.player.heal(SAVESTATE.inventory.consumable.data["healing"])
            if SAVESTATE.inventory.consumable.count > 1:
                SAVESTATE.inventory.consumable.count -= 1
                SAVESTATE.inventory.consumable.update_surface()
            else: SAVESTATE.inventory.set(consumable = None)
            GLOBALS.update_view = True

# Use item in PRIMARY slot (attack)
def use_primary():
    if SAVESTATE.inventory.primary:
        if "damage" in SAVESTATE.inventory.primary.data:
            for e in GLOBALS.level.enemies:
                player_size = GLOBALS.player.surface.size
                start = (GLOBALS.player.pos[0] + player_size[0] // 2, GLOBALS.player.pos[1] + player_size[1] // 2)
                target = (e.pos[0] + e.surface.size[0] // 2, e.pos[1] + e.surface.size[1] // 2)
                dx = target[0] - start[0]
                dy = target[1] - start[1]
                is_hit = False
                if GLOBALS.player.facing == "front":
                    if -(player_size[0] * 2) < dx < (player_size[0] * 2):
                        if 0 < dy < player_size[1] * 2:
                            is_hit = True
                elif GLOBALS.player.facing == "back":
                    if -(player_size[0] * 2) < dx < (player_size[0] * 2):
                        if 0 > dy > -(player_size[1] * 2):
                            is_hit = True
                elif GLOBALS.player.facing == "right":
                    if -(player_size[1] * 2) < dy < (player_size[1] * 2):
                        if 0 < dy < player_size[1] * 2:
                            is_hit = True
                elif GLOBALS.player.facing == "left":
                    if -(player_size[1] * 2) < dy < (player_size[1] * 2):
                        if 0 > dy > -(player_size[1] * 2):
                            is_hit = True
                if is_hit:
                    if e.damage(SAVESTATE.inventory.primary.data["damage"]):
                        for i in e.drops:
                            GLOBALS.player.collect_item(i)
                        GLOBALS.level.enemies.remove(e)
                GLOBALS.update_view = True

# Advance to the next level
def advance_level():
    if len(GLOBALS.level.enemies) > 0:
        load_dialog(MSG["level.advance.kill_required"])
    else:
        GLOBALS.level_change = True
        SAVESTATE.set(level_id = GLOBALS.level.next_level)

# Handle game over
def game_over():
    GLOBALS.game_over = True


# Setup Global Variables
GLOBALS = Enum()

GLOBALS.set(main_loop = True)
GLOBALS.set(in_menu = True)
GLOBALS.set(in_level_select = False)
GLOBALS.set(in_level = False)
GLOBALS.set(in_credits = False)
GLOBALS.set(game_over = False)
GLOBALS.set(game_paused = False)
GLOBALS.set(level = None)
GLOBALS.set(player = None)
GLOBALS.set(update_view = True)
GLOBALS.set(level_change = False)
GLOBALS.set(in_action_menu = False)
GLOBALS.set(active_interactable_id = None)
GLOBALS.set(action_menu = None)
GLOBALS.set(in_container = False)
GLOBALS.set(open_container = None)
GLOBALS.set(dialog = [].copy())
GLOBALS.set(dialog_id = -1)
GLOBALS.set(dialog_anmiation_frame = -1)

GLOBALS.set(dev = False)


# Setup the initial save state
DEFAULT_SAVESTATE = Enum()

DEFAULT_SAVESTATE.set(name = "")
DEFAULT_SAVESTATE.set(level_id = "01")
DEFAULT_SAVESTATE.set(xp = 0)
DEFAULT_SAVESTATE.set(hp = 100)
DEFAULT_SAVESTATE.set(inventory = Inventory().initialize())

# Load savestate from file if available
SAVESTATE = load_savestate(default = DEFAULT_SAVESTATE)
save_savestate(SAVESTATE)

CLOCK = pg.time.Clock()
    


'''
=========
MAIN LOOP
=========
'''
while GLOBALS.main_loop:
    '''======
    MAIN MENU
    ======'''
    if GLOBALS.in_menu:
        screen_objects = setup_menu()

        while GLOBALS.in_menu:
            CLOCK.tick(FPS)
            # Update Graphics View
            if GLOBALS.update_view:
                draw__clean(COLORS.brown)
                draw(screen_objects.title)
                draw(screen_objects.play)
                draw(screen_objects.settings)
                draw(screen_objects.quit)
                draw__window()
                GLOBALS.update_view = False

            # Check for Inputs
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    GLOBALS.in_menu = False
                    GLOBALS.main_loop = False

                if event.type == pg.MOUSEBUTTONDOWN:
                    if screen_objects.quit.get_mouse_collision():
                        GLOBALS.in_menu = False
                        GLOBALS.main_loop = False
                    if screen_objects.play.get_mouse_collision():
                        GLOBALS.in_menu = False
                        GLOBALS.in_level_select = True
                    GLOBALS.update_view = True

                if event.type == pg.MOUSEMOTION:
                    GLOBALS.update_view = True
                
                if event.type == pg.WINDOWFOCUSGAINED:
                    GLOBALS.update_view = True

    '''=========
    LEVEL SELECT
    ========='''
    if GLOBALS.in_level_select:
        screen_objects = setup_level_select()

        while GLOBALS.in_level_select:
            CLOCK.tick(FPS)
            # Update Graphics View
            if GLOBALS.update_view:
                draw__clean(COLORS.brown)
                draw(screen_objects.title)
                draw(screen_objects.subtitle)
                draw(screen_objects.cont)
                draw(screen_objects.restart)
                draw(screen_objects.back)
                draw__window()
                GLOBALS.update_view = False


            # Check for Inputs
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    GLOBALS.in_level_select = False
                    GLOBALS.main_loop = False

                if event.type == pg.MOUSEBUTTONDOWN:
                    if screen_objects.back.get_mouse_collision():
                        GLOBALS.in_level_select = False
                        GLOBALS.in_menu = True
                    elif screen_objects.cont.get_mouse_collision():
                        SAVESTATE = load_savestate()
                        GLOBALS.in_level_select = False
                        GLOBALS.in_level = True
                    elif screen_objects.restart.get_mouse_collision():
                        SAVESTATE = DEFAULT_SAVESTATE
                        GLOBALS.in_level_select = False
                        GLOBALS.in_level = True
                    GLOBALS.update_view = True

                if event.type == pg.MOUSEMOTION:
                    GLOBALS.update_view = True
                
                if event.type == pg.WINDOWFOCUSGAINED:
                    GLOBALS.update_view = True
            
    '''=====
    IN LEVEL
    ====='''
    if GLOBALS.in_level:
        screen_objects, GLOBALS.level, GLOBALS.player = setup_level(SAVESTATE.level_id)

        while GLOBALS.in_level and not GLOBALS.level_change:
            CLOCK.tick(FPS)
            # Update Graphics View
            if GLOBALS.update_view:
                
                draw__clean()
                background_pos = GLOBALS.player.get_background_pos()
                draw(screen_objects.background.set_pos(background_pos))
                
                draw_hitboxes(screen_objects)
                
                # draw InteractableObjects
                for i in GLOBALS.level.interactable_objects:
                    draw(i.get_screen_object().set_pos((i.pos[0] + background_pos[0], i.pos[1] + background_pos[1])))
                
                # draw Enemies
                for i in GLOBALS.level.enemies:
                    if i.triggered:
                        draw(i.get_screen_object().set_pos((i.pos[0] + background_pos[0], i.pos[1] + background_pos[1])))
                        
                draw(GLOBALS.player.get_screen_object())
                
                draw_inventory()
                draw_hp()
                
                draw_dialog()
                
                # draw ActionMenu view
                if GLOBALS.in_action_menu:
                    draw(GLOBALS.action_menu.get_screen_object())
                    for i in GLOBALS.action_menu.buttons:
                        draw(i)
                
                # draw ItemContainer view
                if GLOBALS.in_container:
                    draw(GLOBALS.open_container.get_screen_object())
                    for i in GLOBALS.open_container.buttons:
                        draw(i)
                
                # draw pause menu
                if GLOBALS.game_paused:
                    draw(pause_menu_objects.overlay)
                    
                    draw(pause_menu_objects.title)
                    draw(pause_menu_objects.cont)
                    draw(pause_menu_objects.quit)
                    
                # draw game over screen
                if GLOBALS.game_over:
                    draw(ScreenObject(Surface((WIDTH, HEIGHT), Color(0, 0, 0, 127))).set((0, 0), 7))
                    draw(ScreenObject(Text(MSG["game_over"], COLORS.red, font_size=3)).set((WIDTH // 2, HEIGHT // 2), 7, (True, True)))
                
                draw__window()
                GLOBALS.update_view = False
                
                if GLOBALS.game_over:
                    time.sleep(5)
                    GLOBALS.in_level = False
                    GLOBALS.in_menu = True
            
            if not GLOBALS.game_paused:
                # advance the dialog text animation
                if GLOBALS.dialog_animation_frame >= 0:
                    if GLOBALS.dialog_animation_frame < len(GLOBALS.dialog[GLOBALS.dialog_id]):
                        GLOBALS.dialog_animation_frame += 1
                        GLOBALS.update_view = True
                
                # move enemies toward the player
                for e in GLOBALS.level.enemies:
                    if e.triggered:
                        if e.pursuit:
                            e.current_move_timeout -= 1
                            if e.current_move_timeout <= 0:
                                e.calculate_move()
                                GLOBALS.update_view = True
                        e.update_attack_animation()
                    elif e.check_trigger():
                        e.triggered = True
            
            # Check for hold buttons for movement
            if not GLOBALS.game_paused:
                if pg.key.get_pressed()[pg.K_w]:
                    GLOBALS.player.move((0, -GLOBALS.level.movement_speed))
                    GLOBALS.update_view = True
                if pg.key.get_pressed()[pg.K_s]:
                    GLOBALS.player.move((0, GLOBALS.level.movement_speed))
                    GLOBALS.update_view = True
                if pg.key.get_pressed()[pg.K_a]:
                    GLOBALS.player.move((-GLOBALS.level.movement_speed, 0))
                    GLOBALS.update_view = True
                if pg.key.get_pressed()[pg.K_d]:
                    GLOBALS.player.move((GLOBALS.level.movement_speed, 0))
                    GLOBALS.update_view = True
            
            # Check for inputs
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    GLOBALS.in_level = False
                    GLOBALS.main_loop = False
                
                if event.type == pg.WINDOWFOCUSGAINED:
                    GLOBALS.update_view = True
                
                if event.type == pg.MOUSEMOTION:
                    GLOBALS.update_view = True
                    
                if event.type == pg.MOUSEBUTTONDOWN:
                    # if in the pause menu
                    if GLOBALS.game_paused:
                        if pause_menu_objects.cont.get_mouse_collision():
                            GLOBALS.game_paused = not GLOBALS.game_paused
                        elif pause_menu_objects.quit.get_mouse_collision():
                            GLOBALS.in_level = False
                            GLOBALS.level = None
                            GLOBALS.game_paused = False
                            GLOBALS.in_menu = True
                            
                    # if in an ActionMenu view
                    elif GLOBALS.in_action_menu:
                        for b in GLOBALS.action_menu.buttons:
                            if b.get_mouse_collision():
                                activate_action(b.content)
                                
                    # if in an ItemContainer view
                    elif GLOBALS.in_container:
                        for b in GLOBALS.open_container.buttons:
                            if b.get_mouse_collision():
                                if GLOBALS.open_container.remove_item(b.item):
                                    i = GLOBALS.player.collect_item(b.item)
                                    if i: GLOBALS.open_container.add_item(i)
                                    GLOBALS.open_container.update_surface()
                            
                    GLOBALS.update_view = True
                
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        GLOBALS.game_paused = not GLOBALS.game_paused
                        if GLOBALS.game_paused:
                            pause_menu_objects = setup_pause_menu()
                        GLOBALS.update_view = True
                    if event.key == pg.K_F2:
                        screenshot("1.0")
                        
                    if not GLOBALS.game_paused:
                        if GLOBALS.dialog_id >= 0:
                            if event.key == pg.K_SPACE:
                                advance_dialog()
                                
                        if event.key == pg.K_q:
                            use_consumable()
                            
                        if event.key == pg.K_e:
                            use_primary()
                            
                    GLOBALS.update_view = True

        GLOBALS.level_change = False
        
        '''====
        CREDITS
        ===='''
        if SAVESTATE.level_id == "credits":
            pages = setup_credits()
            
            page_id = 0
            
            while GLOBALS.in_credits:
                CLOCK.tick(30)
                        
                if GLOBALS.update_view:
                    draw__clean()
                    
                    for so in pages[page_id]:
                        draw(so)
                    
                    draw__window()
                    
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        GLOBALS.in_credits = False
                        GLOBALS.main_loop = False
                    
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_SPACE:
                            page_id += 1
                            if page_id >= len(pages):
                                GLOBALS.in_credits = False
                                GLOBALS.in_menu = True
                                
                        if event.key == pg.K_ESCAPE:
                            GLOBALS.in_credits = False
                            GLOBALS.in_menu = True
                            
                        GLOBALS.update_view = True
                
            SAVESTATE = load_savestate(SAVESTATE)
















pg.quit()

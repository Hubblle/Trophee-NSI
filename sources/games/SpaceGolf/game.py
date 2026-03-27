# Importation des librairies

import pygame
from os import path
from .physics import Vector, GraphicalCelestialBody, Earth
from utils import loadAssetsFolder, RangeInput, PopUp, SpriteSheet, Button, LoadedFont
from json import dump
from math import log10

WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_SIZE = (1600, 900)
FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script

mouse_pos = {"x": 0, "y": 0}
cam_x = 0
cam_y = 0
event_list = []  # Liste des évènements
scale = 100000  # 1 pixel = 100 000 mètres
time_scale = 6000  # 1 seconde dans la réalité correspond à 6000 seconde dans le jeu

surface = pygame.Surface(WINDOW_SIZE)  # La surface utilisée dans la fonction display

# Préciser le type de la variable est facultatif mais permet à l'éditeur de code de proposer l'auto-complétion
# Les variables initialisées à None sont des variables globales qui seront initialisées dans la fonction load

earth: Earth = None  # La planète Terre, initialisée dans la fonction load
celestial_bodies: list[GraphicalCelestialBody] = []
worm_hole: GraphicalCelestialBody = None
launching = False
launch_speed = Vector()
zoom_input: RangeInput = None
time_input: RangeInput = None
level_end: PopUp = None
lost: PopUp = None
background: pygame.Surface = None
stars_images: dict[str, pygame.Surface | SpriteSheet] = {}
levels: list[dict] = None
level = 0
max_trials = None
trials = None
fonts: LoadedFont = None
restart_button: Button = None
previous_button: Button = None
next_button: Button = None
editing = False
mode_button: RangeInput = None
edit_target: GraphicalCelestialBody = None
add_button: Button = None
remove_button: Button = None
mass_input: RangeInput = None
radius_input: RangeInput = None
type_input: RangeInput = None
trials_input: RangeInput = None
edited = False
music: pygame.Sound = None
click_sound: pygame.Sound = None
lost_sound: pygame.Sound = None
launch_sound: pygame.Sound = None
explosion_sound: pygame.Sound = None

# On définit les fonctions secondaires

def setScale(value: int) -> None:
    """
    Change l'échelle du rendu en gardant la caméra centré au même endroit.

    :param value: Nouvelle valeur de scale
    :type value: int
    """
    global scale, cam_x, cam_y
    x = scale * cam_x  # cam_x est en pixels, x est en mètres
    y = scale * cam_y  # cam_y est en pixels, y est en mètres
    scale = value
    cam_x = x // scale
    cam_y = y // scale


def screenPosition(x: int, y: int) -> tuple:
    """
    Retourne la position d'un élément relative à l'écran depuis sa position 
    absolue (en m) et en prenant en compte le zoom et la position de la caméra.

    :param x: Abscisse absolue de l'élément
    :type x: int (m)
    :param y: Ordonnée absolue de l'élément
    :type y: int (m)
    :return: La position relative au coin supérieur gauche de l'écran
    :rtype: tuple[int, int]
    """
    return WINDOW_WIDTH//2-cam_x+x//scale, WINDOW_HEIGHT//2-cam_y+y//scale


def loadLevel(index: int) -> None:
    """
    Charge le niveau correspondant au paramètre index.

    :param index: Index du niveau commençant à 0
    :type index: int
    """
    global cam_x, cam_y, max_trials, trials, launching
    cam_x = cam_y = 0
    level = levels[index]
    max_trials = trials = level["trials"]
    launching = False
    mode_button.value = 0

    earth.reset()
    earth.other_bodies.clear()
    earth.addInteraction(worm_hole)

    wx, wy = level["worm_hole"]
    worm_hole.x = wx
    worm_hole.y = wy
    
    celestial_bodies.clear()
    for x, y, mass, radius, costume in level["suns"]:
        sun = GraphicalCelestialBody(x, y, mass, radius, stars_images["suns"][costume], surface, screenPosition)
        earth.addInteraction(sun)
        celestial_bodies.append(sun)
    
    for x, y, mass, radius in level["black_holes"]:
        black_hole = GraphicalCelestialBody(x, y, mass, radius, stars_images["black_hole"], surface, screenPosition, True)
        earth.addInteraction(black_hole)
        celestial_bodies.append(black_hole)


def saveLevelInMemory() -> None:
    """
    Sauvegarde le niveau actuel dans la liste 'levels'.
    """
    data = levels[level]
    data["worm_hole"] = [worm_hole.x, worm_hole.y]
    data["trials"] = max_trials
    data["suns"] = [[s.x, s.y, s.mass, s.radius, stars_images["suns"].index(s.original_image)] for s in celestial_bodies if not s.is_black_hole]
    data["black_holes"] = [[h.x, h.y, h.mass, h.radius] for h in celestial_bodies if h.is_black_hole]


def saveLevelsToDisk() -> None:
    """
    Sauvegarde les niveaux sur le disque.
    """
    json_path = path.join(FOLDER_PATH, "assets", "json", "levels.json")
    if not path.exists(json_path):
        open(json_path, "x")
    with open(json_path, "w") as f:
        dump(levels, f, indent=2)


def setTargetTo(body: GraphicalCelestialBody) -> None:
    """
    Affectue body à edit_target et change les paramètres pour les faire correspondre.

    :param body: L'astre à sélectionner
    :type body: GraphicalCelestialBody
    """
    global edit_target
    edit_target = body
    mass_input.value = log10(body.mass) - (8 if body.is_black_hole else 0)
    radius_input.value = log10(body.radius)
    type_input.value = 3 if body.is_black_hole else stars_images["suns"].index(body.original_image)


# On définit les 6 fonctions principales

def load() -> None:
    """
    La fonction load charge les assets.
    """

    # On définit les fonctions qui vont servir de callback dans les boutons

    def convertTime(value: int) -> str:
        if value >= 3600:
            return f"1s : {value//3600}h {(value%3600)//60}min"
        elif value >= 60:
            return f"1s : {value//60}min"
        else:
            return f"1s : {value}s"
    
    def convertDistance(value: int) -> str:
        if value >= 1e9:
            return f"1px : {round(value/1e9)} x 10^6 km"
        elif value >= 1e6:
            return f"1px : {round(value/1e6)} x 10^3 km"
        elif value >= 1000:
            return f"1px : {value//1000} km"
        else:
            return f"1px : {value} m"
    
    def onClickHome() -> None:
        click_sound.play()
        level_end.displayed = False
        event_list.append({"type": "quit"})
    
    def onClickNext() -> None:
        global level, edited
        click_sound.play()
        if edited:
            saveLevelInMemory()
            saveLevelsToDisk()
            edited = False
        if level+1 < len(levels):
            level += 1
        elif editing:
            level += 1
            levels.append({"worm_hole": [2e8, 0], "suns": [], "black_holes": [], "trials": 3})
        level_end.displayed = False
        loadLevel(level)

    def onClickPrevious() -> None:
        global level, edited
        click_sound.play()
        if edited:
            saveLevelInMemory()
            saveLevelsToDisk()
            edited = False
        level = max(level - 1, 0)
        level_end.displayed = False
        loadLevel(level)
    
    def onClickRestart() -> None:
        global cam_x, cam_y, trials
        click_sound.play()
        cam_x = cam_y = 0
        trials = max_trials
        earth.reset()
        lost.displayed = False
    
    def onClickAdd() -> None:
        global edit_target
        click_sound.play()
        body = GraphicalCelestialBody(cam_x*scale, cam_y*scale, 1e25, 7e7, stars_images["suns"][0], surface, screenPosition)
        celestial_bodies.append(body)
        earth.addInteraction(body)
        setTargetTo(body)
    
    def onClickRemove() -> None:
        global edit_target
        click_sound.play()
        if edit_target in celestial_bodies:
            celestial_bodies.remove(edit_target)
        if edit_target in earth.other_bodies:
            earth.other_bodies.remove(edit_target)
        edit_target = None
    
    global background, zoom_input, time_input, earth, worm_hole, level_end, levels, fonts, restart_button, previous_button, \
        next_button, mode_button, add_button, mass_input, radius_input, type_input, lost, trials_input, remove_button, \
        lost_sound, click_sound, launch_sound, music, explosion_sound
    
    assets = {}
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "assets"))  # On utilise la fonction utilitaire loadAssetsFolder définie dans sources/utils.py
    levels = assets["json"]["levels.json"]

    # On charge les soleils
    suns = []
    stars_images["suns"] = suns
    suns.append(assets["images"]["sun1[SPRITESHEET;335;10].png"])
    suns.append(assets["images"]["sun2[SPRITESHEET;465;10].png"])
    suns.append(assets["images"]["sun3[SPRITESHEET;156;10].png"])

    # On charge le trou de ver
    stars_images["worm_hole"] = assets["images"]["worm_hole[SPRITESHEET;400;20].png"]

    # On charge le trou noir
    stars_images["black_hole"] = assets["images"]["black_hole[SPRITESHEET;508;20].png"]

    # On créé le trou de ver
    worm_hole = GraphicalCelestialBody(0, 0, 1e33, 2e7, stars_images["worm_hole"], surface, screenPosition, True)
    
    # On créé la Terre
    explosion = assets["images"]["explosion[SPRITESHEET;151;24].png"]
    earth = Earth(0, 0, assets["images"]["earth.png"], surface, screenPosition, worm_hole, explosion)

    # On charge le fond
    background = assets["images"]["space.png"]

    level_end = PopUp(surface, WINDOW_WIDTH//2, WINDOW_HEIGHT//2, assets["images"]["popup.png"],
                      Button(230, 120, assets["images"]["home.png"], onClickHome),
                      Button(-212, 120, assets["images"]["next.png"], onClickNext))

    lost = PopUp(surface, WINDOW_WIDTH//2, WINDOW_HEIGHT//2, assets["images"]["lose.png"],
                      Button(230, 125, assets["images"]["home.png"], onClickHome),
                      Button(-200, 125, assets["images"]["retry.png"], onClickRestart))

    # Une fois les assets chargées on peut créer les RangeInput
    fonts = assets["fonts"]["inter.ttf"]
    zoom_input = RangeInput(36, WINDOW_HEIGHT-36, 160, (50000, 500000, 10000), surface, convertDistance, fonts.getFont(24), 12, 100000)
    time_input = RangeInput(230, WINDOW_HEIGHT-36, 160, (600, 14400, 600), surface, convertTime, fonts.getFont(24), 12, 5400)
    mode_button = RangeInput(WINDOW_WIDTH-120, 36, 60, (0, 1), surface, lambda value: f"Mode : {"édition" if value else "jeu"}", fonts.getFont(18), 9, 0)
    mass_input = RangeInput(WINDOW_WIDTH-150, 100, 100, (24, 28, 0.1), surface, lambda value: f"Masse : {10**(value if type_input.value < 3 else value+8):.2g} kg", fonts.getFont(20), 10, 25)
    radius_input = RangeInput(WINDOW_WIDTH-150, 170, 100, (7.3, 8.3, 0.05), surface, lambda value: f"Rayon : {10**value:.2g} m", fonts.getFont(20), 10, 7.7)
    type_input = RangeInput(WINDOW_WIDTH-150, 240, 100, (0, 3), surface, lambda i: f"Type : {f"étoile#{i+1}" if i < 3 else "trou noir"}", fonts.getFont(20), 10, 0)
    trials_input = RangeInput(WINDOW_WIDTH-280, 36, 100, (1, 20), surface, lambda value: f"Essais max : {value}", fonts.getFont(18), 9, 1)

    # On créé les boutons cliquables
    restart_button = Button(WINDOW_WIDTH//2, 30, assets["images"]["restart.png"], onClickRestart, surface)
    previous_button = Button(WINDOW_WIDTH//2 - 60, 30, assets["images"]["previous_button.png"], onClickPrevious, surface)
    next_button = Button(WINDOW_WIDTH//2 + 60, 30, assets["images"]["next_button.png"], onClickNext, surface)
    add_button = Button(WINDOW_WIDTH-340, 36, assets["images"]["add.png"], onClickAdd, surface)
    remove_button = Button(WINDOW_WIDTH-400, 36, assets["images"]["remove.png"], onClickRemove, surface)

    # On récupère les sons
    lost_sound  = assets["sounds"]["lost.mp3"]
    click_sound = assets["sounds"]["click.mp3"]
    music = assets["sounds"]["music.mp3"]
    launch_sound = assets["sounds"]["launch.mp3"]
    explosion_sound = assets["sounds"]["explosion.mp3"]


def init() -> None:
    """
    Initialise/réinitialise le mini-jeu
    """
    global level, edited
    level = 0
    loadLevel(0)
    edited = False
    level_end.displayed = False
    lost.displayed = False
    event_list.clear()
    level_end.displayed = False
    zoom_input.value = 100000
    time_input.value = 5400
    music.play(-1)


def tick(keys: dict, mouse: dict) -> None:
    """
    Docstring for tick
    
    :param keys: Dictionnaire des touches pressées par l'utilisateur. Les valeurs correspondent à la durée de la pression de la touche. Exemple `{pygame.K_UP: 8, pygame.K_LEFT: 0, pygame.K_RIGHT: 1}`
    :type keys: dict
    :param mouse: Dictionnaire contenant les informations liées à la souris `{'x': int, 'y'; int, 'click': list[int, int, int]}`
    :type mouse: dict
    """
    global mouse_pos, cam_x, cam_y, launching, scale, time_scale, trials, editing, edited, max_trials, edit_target, trials

    mouse_click = mouse["click"][0]  # On utilise une variable temporaire pour pouvoir stopper la propagation d'un clic si celui-ci est intercepté par un bouton

    # Simulation des pop-up
    if level_end.displayed:
        level_end.tick(mouse["x"], mouse["y"], mouse_click)
        mouse_click = 0
    if lost.displayed:
        lost.tick(mouse["x"], mouse["y"], mouse_click)
        mouse_click = 0
    
    # Simulation des boutons
    param = (mouse["x"], mouse["y"]), mouse_click
    zoom_input.tick(*param)
    setScale(zoom_input.value)
    time_input.tick(*param)
    time_scale = time_input.value
    mode_button.tick(*param)
    editing = bool(mode_button.value)
    if not editing:
        edit_target = None
    if mode_button.changed and editing:
        edited = True
    if zoom_input.clicked or time_input.clicked or mode_button.clicked:
        mouse_click = 0
    
    # On affiche les entrées numériques servant à configurer un astre en mode edit
    if edit_target and edit_target is not worm_hole:
        mass_input.tick(*param)
        mass = round(10**(mass_input.value + (8 if type_input.value == 3 else 0)))
        if mass != edit_target.mass:
            edit_target.mass = mass
        
        radius_input.tick(*param)
        radius = round(10**radius_input.value)
        if radius != edit_target.radius:
            edit_target.radius = radius
            edit_target.images.clear()
        
        type_input.tick(*param)
        if type_input.changed:
            if type_input.value == 3:
                edit_target.original_image = stars_images["black_hole"]
                edit_target.is_black_hole = True
                edit_target.images.clear()
            else:
                edit_target.original_image = stars_images["suns"][type_input.value]
                edit_target.is_black_hole = False
                edit_target.images.clear()
        
        if mass_input.clicked or radius_input.clicked or type_input.clicked:
            mouse_click = 0
    
    param = (mouse["x"], mouse["y"], mouse_click)
    if any((restart_button.tick(*param),
           previous_button.tick(*param),
           next_button.tick(*param))):
        mouse_click = 0
    
    if editing:
        trials_input.tick((mouse["x"], mouse["y"]), mouse_click)
        if trials_input.changed:
            max_trials = trials_input.value
            trials = min(trials, max_trials)
        if trials_input.clicked:
            mouse_click = 0
        if add_button.tick(*param):
            mouse_click = 0
        if edit_target and edit_target is not worm_hole:
            if remove_button.tick(*param):
                mouse_click = 0

    if trials > 0 or editing:
        if launching:
            earth_x, earth_y = screenPosition(earth.x, earth.y)
            launch_speed.coordinates = earth_x - mouse["x"], earth_y - mouse["y"]
            if mouse_click == 0:
                launching = False
                launch_sound.play()
                earth.speed.direction = launch_speed.direction
                # On convertit la distance du lancement en une vitesse de lancement en m/s avec l'échelle suivante : 7500 m = 1 m/s
                earth.speed.magnitude = launch_speed.magnitude * scale / 7500
                earth.locked = False
                if not editing:
                    trials -= 1
        else:
            # La souris vient dêtre cliquée
            if mouse_click == 1:
                earth_x, earth_y = screenPosition(earth.x, earth.y)
                # La souris touche la Terre
                if (mouse["x"] - earth_x)**2 + (mouse["y"] - earth_y)**2 < (6.2e6/scale)**2:
                    earth.stop()
                    launching = True
                    earth.locked = True
                    mouse_click = 0
    
    # On sélectionne/désélectionne un astre en mode edit
    if mouse_click == 1 and editing:
        edit_target = None
        for body in (*celestial_bodies, worm_hole):
            if body.isTouchingMouse(mouse["x"], mouse["y"], scale):
                setTargetTo(body)
                break

    # Si le clic gauche de la souris est pressé, on compare sa position à la précédente pour faire déplacer la caméra
    if mouse_click > 0:
        if edit_target and edit_target.isTouchingMouse(mouse["x"], mouse["y"], scale):
            edit_target.x += (mouse["x"] - mouse_pos["x"]) * scale
            edit_target.y += (mouse["y"] - mouse_pos["y"]) * scale
        elif not launching:
            cam_x += mouse_pos["x"] - mouse["x"]
            cam_y += mouse_pos["y"] - mouse["y"]
    
    if earth.exploding:
        if not lost.displayed and earth.explosion_end:
            lost.displayed = True
            lost_sound.play()
    else:
        earth.move(1/40, time_scale)
        if earth.collide():
            explosion_sound.play()
    if earth.fallen:  # Tombée dans un trou noir
        if earth.success:
            if editing:
                earth.reset()
            else:
                level_end.displayed = True
        else:
            if not lost.displayed:
                lost_sound.play()
                lost.displayed = True

    # Mis à jour de la position de la souris

    mouse_pos["x"], mouse_pos["y"] = mouse["x"], mouse["y"]

    # Option pour mettre en pause

    if keys[pygame.K_ESCAPE]:
        event_list.append({"type": "pause"})


def display() -> pygame.Surface:
    """
    Docstring for display
    
    :return: L'affichage du mini-jeu
    :rtype: pygame.Surface
    """
    surface.fill((0, 0, 0))
    # On remplit le fond en dupliquant une image de l'espace
    for x in range(round(cam_x*scale*-1.5e-7)%background.width-background.width, WINDOW_WIDTH, background.width):
        for y in range(round(cam_y*scale*-1.5e-7)%background.height-background.height, WINDOW_HEIGHT, background.height):
            surface.blit(background, (x, y))
    
    # On ajoute la planète Terre, les soleils, le trou de ver et les trous noirs
    for body in (*celestial_bodies, worm_hole):
        body.display(scale)
        if body is edit_target:
            pygame.draw.circle(surface, (255, 255, 255), screenPosition(body.x, body.y), round(body.radius/scale)+50, 10)

    if launching:
        pygame.draw.line(surface, (255, 0, 0), screenPosition(earth.x, earth.y), (mouse_pos["x"], mouse_pos["y"]), 4)
    
    if not earth.fallen:
        earth.display(scale)

    # On affiche les boutons
    zoom_input.display()
    time_input.display()
    mode_button.display()

    if edit_target and edit_target is not worm_hole:
        mass_input.display()
        radius_input.display()
        type_input.display()

    restart_button.display()
    previous_button.display()
    next_button.display()
    if editing:
        add_button.display()
        trials_input.display()
        if edit_target and edit_target is not worm_hole:
            remove_button.display()

    # On affiche le nombre d'essais restants
    font = fonts.getFont(26)
    text = font.render(f"Essais restants : {trials} sur {max_trials}", True, (255, 255, 255))
    surface.blit(text, (36, WINDOW_HEIGHT - text.height - 85))

    # On affiche le numéro du niveau
    font = fonts.getFont(24)
    text = font.render(f"Niveau {level+1} / {len(levels)}", True, (255, 255, 255))
    surface.blit(text, (WINDOW_WIDTH//2-text.width//2, 60))

    # On affiche les pop-up
    if level_end.displayed:
        level_end.display()
    if lost.displayed:
        lost.display()
    
    return surface


def events() -> list:
    """
    Docstring for events
    
    :return: Retourne la liste des évènements s'étant produit dans le mini-jeu. Exemple `['quit']`
    :rtype: list[str]
    """
    events_copy = event_list.copy()
    event_list.clear()  # On vide la liste des évènements pour ne pas les renvoyer à nouveau au prochain appel
    return events_copy


def quit() -> None:
    music.stop()
    if edited:
        saveLevelInMemory()
        saveLevelsToDisk()
    
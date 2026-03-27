# Importation des librairies

import pygame
from os import scandir, path
from sys import exit, version_info

# pygame et pygame-ce utilisent le même nom de module et de dossier, cette sécurité permet d'éviter des erreurs inexpliquées plus tard
if not hasattr(pygame.Surface, "width"):
    print("\n[Erreur] Vous utilisez la version régulière de pygame au lieu de pygame-ce")
    print("Désinstallez pygame et pygame-ce puis réinstallez pygame-ce\n")
    exit()

# Ce projet fonctionne mal avec les versions de python précédant la 3.12
if not (version_info[0] == 3 and version_info[1] >= 12 or version_info[0] > 3):
    print("\n[Erreur] Vous utilisez une version de python précédant la 3.12")
    print("Installez une version de python >= 3.12 pour lancer ce projet")

from utils import loadAssetsFolder, loadGame, RangeInput, loadingBar, Button, PopUp, renderMultipleLines

# Constantes

PRELOAD = True  # Si True : on charge les assets de tous les jeux au lancement, sinon seulement au démarrage du mini-jeu

# Définition des fonctions

def playGame(game: dict, window: pygame.Surface, assets: dict) -> bool:
    """
    playGame est une fonction bloquante qui va lancer le jeu passé en paramètre puis gérer tous
    les échanges de données entre ce script et le mini-jeu.
    La fonction s'arrêtera quand le mini-jeu renverra l'évènement de type 'quit' ou quand l'utilisateur fermera la fenêtre.
    
    :param game: Un dictionnaire contenant les clés 'config', 'menu_background', 'tick', 'display', 'events', 'init' et 'load'
    :type game: dict
    :param window: La fenêtre sur laquelle va être affiché le mini-jeu
    :type window: pygame.Surface
    :param assets: Les ressources du menu (images, sons et polices)
    :type assets: dict[str, dict | pygame.Surface | pygame.mixer.Sound]
    :return: True si l'utilisateur a fermé la fenêtre sinon False
    :rtype: bool
    """
    CONFIG: dict = game["config"]
    SPEED = CONFIG["simulation_speed"]
    RENDERING_WIDTH = CONFIG["width"]
    RENDERING_HEIGHT = CONFIG["height"]
    FPS = CONFIG.get("FPS", False)
    FPS_COLOR = CONFIG.get("FPS_input", {})
    KEYS = [getattr(pygame, key, -1) for key in CONFIG["keys"]]  # On passe d'une liste de str (ex : 'K_a') à une liste de constante de pygame (ex : pygame.K_a)
    WHEEL_MOTION = CONFIG.get("wheel_motion", False)

    pygame.display.set_caption("Physics.play - " + CONFIG["name"])

    # On affecte les fonctions principales à des variables pour faciliter leur utilisation
    tick = game["tick"]
    display = game["display"]
    events = game["events"]
    init = game["init"]
    load = game["load"]
    quit = game.get("quit", lambda: None)
    
    # Si le jeu n'a encore jamais été chargé, on le fait
    if not game["loaded"]:
        load()
        game["loaded"] = True
    
    init()  # On initialise le mini-jeu

    keys_to_send = {key: 0 for key in KEYS}  # Dictionnaire qui va être envoyé à la fonction tick du mini-jeu
    mouse = {"x": 0, "y": 0, "click": [0, 0, 0]}

    fps = SPEED  # Nombre de rafraichissement de l'écran par seconde, varie de 1 à SPEED
    cooldown_before_render = 0  # Augmente de fps/SPEED à chaque itération de la boucle. L'écran sera actualisé à chaque fois qu'il atteint 1
    clock = pygame.time.Clock()  # Pour réguler la vitesse d'une boucle

    # On créé une entrée numérique pour que l'utilisateur puisse gérer ses FPS sur n'importe quel jeu
    font = assets["fonts"]["inter.ttf"].getFont(18)
    fps_input = RangeInput(20, 30, 140, (5, SPEED), window, lambda value: f"FPS: {value}", font, 8, min(30, SPEED), **FPS_COLOR)

    # On créé la pop-up qui s'affiche quand l'utilisateur met un mini-jeu en pause
    def onClickResume() -> None:  # Callback du bouton 'reprendre'
        pause.displayed = False
        mouse["click"][0] = 0
    
    def onClickQuit() -> None:  # Callback du bouton 'quitter'
        pause.displayed = False
        pause.quit = True
    
    pause_background = assets["images"]["pause.png"]
    pause_scale = RENDERING_HEIGHT * 0.8 / pause_background.height  # On calcule le facteur à utiliser pour redimensionner l'image
    pause = PopUp(None, RENDERING_WIDTH//2, RENDERING_HEIGHT//2, pygame.transform.scale_by(pause_background, pause_scale),
                  Button(round(-200*pause_scale), round(100*pause_scale), pygame.transform.scale_by(assets["images"]["resume.png"], pause_scale), onClickResume),
                  Button(round(200*pause_scale), round(100*pause_scale), pygame.transform.scale_by(assets["images"]["quit.png"], pause_scale), onClickQuit))
    pause.quit = False
    shadow = pygame.Surface((RENDERING_WIDTH, RENDERING_HEIGHT), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 100))

    wheel_changes = 0  # Stocke le mouvement de la roulette de la souris

    while True:

        if not pause.displayed:
            # On incrémente la durée de la pression des touches enfoncées
            for key, value in keys_to_send.items():
                if value > 0:
                    keys_to_send[key] += 1

        # Même chose pour les clics de la souris : gauche, roulette, droit

        for i, click in enumerate(mouse["click"]):
            if click > 0:
                mouse["click"][i] += 1

        # Gestion des évènements de la fenêtre

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # L'utilisateur a fermé la fenêtre
                quit()
                return True
            if event.type == pygame.KEYDOWN:  # Une touche a été pressée
                if event.key in KEYS:
                    keys_to_send[event.key] = 1
            elif event.type == pygame.KEYUP:  # Une touche a été relachée
                if event.key in KEYS:
                    keys_to_send[event.key] = 0
            elif event.type == pygame.MOUSEWHEEL:
                wheel_changes += event.y
            elif event.type == pygame.WINDOWSIZECHANGED:
                # On empêche de réduire la taille de la fenêtre en dessous du minimum donné par le fichier 'config.json'
                min_width = CONFIG.get("window_min_width", 360)
                min_height = CONFIG.get("window_min_height", 200)
                width, height = event.x, event.y
                if width < min_width or height < min_height:
                    width = max(width, min_width)
                    height = max(height, min_height)
                    pygame.display.set_mode((width, height), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 1 <= event.button <= 3:
                    mouse["click"][event.button-1] = 1
            elif event.type == pygame.MOUSEBUTTONUP:
                if 1 <= event.button <= 3:
                    mouse["click"][event.button-1] = 0

        # On calcule le ratio à appliquer sur le rendu afin de l'adapter à la taille de la fenêtre
        scale_x = window.width / RENDERING_WIDTH
        scale_y = window.height / RENDERING_HEIGHT
        scale = min(scale_x, scale_y)
        
        # On convertit la position de la souris sur la fenêtre pour qu'elle s'adapte à la taille du mini-jeu
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, mouse_y, = mouse_pos
        mouse_x -= window.width//2 - RENDERING_WIDTH//2 * scale
        mouse_x = round(mouse_x / scale)
        mouse_y -= window.height//2 - RENDERING_HEIGHT//2 * scale
        mouse_y = round(mouse_y / scale)
        mouse_x = min(RENDERING_WIDTH-1, max(0, mouse_x))
        mouse_y = min(RENDERING_HEIGHT-1, max(0, mouse_y))
        mouse["x"], mouse["y"] = mouse_x, mouse_y

        if pause.displayed:

            pause.tick(mouse_x, mouse_y, mouse["click"][0])
            if pause.quit:
                quit()
                return False

        else:
            # On simule les boutons
            fps_input.tick(mouse_pos, mouse["click"][0])
            fps = fps_input.value
            
            # On simule le mini-jeu
            mouse_sent = {"x": mouse["x"], "y": mouse["y"], "click": mouse["click"].copy()}
            if fps_input.clicked:  # Si le bouton est cliqué, on n'envoie pas le clic au mini-jeu
                mouse_sent["click"][0] = 0

            options = {}
            if FPS:
                options["fps"] = clock.get_fps()
            if WHEEL_MOTION:
                options["wheel"] = wheel_changes
            wheel_changes = 0

            tick(keys=keys_to_send, mouse=mouse_sent, **options)

            for event in events():
                if event["type"] == "pause":
                    pause.displayed = True
                elif event["type"] == "quit":  # Le mini-jeu est fini
                    quit()
                    return False

        cooldown_before_render += fps / SPEED
        if cooldown_before_render >= 1:
            cooldown_before_render -= 1

            game_rendering = display()  # On récupère le rendu du mini-jeu
            if pause.displayed:
                game_rendering.blit(shadow, (0, 0))  # On assombrit tout ce qui est derrière la pop-up
                pause.display(game_rendering)

            if game_rendering.size != (RENDERING_WIDTH, RENDERING_HEIGHT):
                print(f"[Erreur] La taille du rendu graphique du mini-jeu '{CONFIG["name"]}' ne correspond pas à sa configuration")
                quit()
                return False
            
            color = CONFIG.get("background_color", (0, 0, 0))
            window.fill(color)  # On efface la fenêtre avec la couleur donnée dans la configuration, par défaut du noir

            # On adapte le rendu à la taille de la fenêtre en préservant son ratio
            game_rendering = pygame.transform.scale_by(game_rendering, scale)

            window.blit(game_rendering, (window.width//2-game_rendering.width//2, window.height//2-game_rendering.height//2))  # On applique le rendu en le centrant

            # On affiche les boutons
            fps_input.display()

            pygame.display.flip()  # On actualise la fenêtre
            
        clock.tick(SPEED)  # On limite la boucle à SPEED tours par seconde


def menu(games: list, window: pygame.Surface, assets: dict, ghost_surface: pygame.Surface = None) -> dict | None:
    """
    menu est une fonction bloquante qui affichera le menu des mini-jeux et s'occupera des interactions avec l'utilisateur.
    
    :param games: Une liste de mini-jeux représentés par un dictionnaire
    :type games: list[dict]
    :param window: La fenêtre sur laquelle va être affiché le menu
    :type window: pygame.Surface
    :param assets: Les ressources du menu (images, sons et polices)
    :type assets: dict[str, dict | pygame.Surface | pygame.mixer.Sound]
    :param ghost_surface: Une image qui s'efface rapidemant à l'apparition du menu
    :type ghost_surface: pygame.Surface | None
    :return: Le jeu sélectionné par l'utilisateur sous forme d'un dictionnaire ou None si l'utilisateur a fermé la fenêtre
    :rtype: dict | None 
    """
    game_idx = 0  # Index du jeu selectionné par rapport à la liste 'games'
    clock = pygame.time.Clock()  # Pour réguler la vitesse d'une boucle

    pygame.display.set_caption("Physics.play")
    
    # On récupère les ressources qui nous intéresse pour le menu
    arrow_right = pygame.transform.scale_by(assets["images"]["arrow.png"], 0.5)
    arrow_left = pygame.transform.flip(arrow_right, True, False)
    arrow_size = arrow_right.get_size()
    
    # On charge les polices
    font = assets["fonts"]["inter.ttf"]

    music = assets["sounds"]["music.mp3"]
    music.play(-1)

    def onClickPlay() -> None:
        play.game = game_idx
    
    play = Button(lambda: window.width//2, lambda: window.height//2, assets["images"]["play.png"], onClickPlay, window)
    play.game = -1

    description = {"game_index": None, "width": None, "surface": None, "y": 40, "shadow": None}
        
    while True:
        
        click = False
        
        # Gestion des évènements de la fenêtre
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # L'utilisateur a fermé la fenêtre
                return None
            if event.type == pygame.KEYDOWN:  # Une touche a été pressée
                # Si c'est la touche 'espace' ou 'entrer' alors on retourne le jeu affiché à l'écran
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    music.stop()
                    return games[game_idx]
                if event.key == pygame.K_LEFT:  # Flèche gauche
                    game_idx = (game_idx - 1) % len(games)
                elif event.key == pygame.K_RIGHT:  # Fléche droite
                    game_idx = (game_idx + 1) % len(games)
            elif event.type == pygame.WINDOWSIZECHANGED:
                # On empêche de réduire la taille de la fenêtre en dessous de 400x320
                width, height = event.x, event.y
                if width < 400 or height < 320:
                    width = max(width, 400)
                    height = max(height, 320)
                    pygame.display.set_mode((width, height), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
        
        game = games[game_idx]
        
        background = game["menu_background"]
        mouse_pos = pygame.mouse.get_pos()
        
        # On calcule le ratio à appliquer sur l'image de fond afin de l'adapter à la taille de la fenêtre
        scale_x = window.width / background.width
        scale_y = window.height / background.height
        
        # On prend le plus grand afin d'être sûr de remplir le fond de la fenêtre même si une partie de l'image risque d'être rognée
        scale = max(scale_x, scale_y)

        play.tick(*mouse_pos, click)
        if play.game != -1:
            music.stop()
            return games[play.game]
        
        # On adapte la hauteur de la description
        if window.height - description["y"] <= mouse_pos[1]:
            description["y"] += round((description["surface"].height - description["y"]) / 5)
        else:
            description["y"] += round((40 - description["y"]) / 5)
        
        # On calcule la position des flèches et on vérifie les collisions avec la souris
        arrow_y = window.height//2-arrow_size[1]//2
        arrow_left_x = 10
        arrow_right_x = window.width - arrow_size[0] - 10
        
        if pygame.Rect(arrow_left_x, arrow_y, *arrow_size).collidepoint(mouse_pos):
            if click:
                game_idx = (game_idx - 1) % len(games)
            arrow_left.set_alpha(245)
        else:
            arrow_left.set_alpha(210)
        
        if pygame.Rect(arrow_right_x, arrow_y, *arrow_size).collidepoint(mouse_pos):
            if click:
                game_idx = (game_idx + 1) % len(games)
            arrow_right.set_alpha(245)
        else:
            arrow_right.set_alpha(210)
        
        window.fill((0, 0, 0))  # On efface tout le précédent contenu de la fenêtre
        
        background = pygame.transform.scale_by(background, scale)  # On adapte le fond à la taille de la fenêtre en préservant son ratio
        window.blit(background, (window.width//2-background.width//2, window.height//2-background.height//2))  # On applique le fond en le centrant
        
        # On assombrit le fond
        shadow = pygame.Surface(window.size, pygame.SRCALPHA)
        shadow.fill((0, 0, 0))
        shadow.set_alpha(50)  # Très transparent
        window.blit(shadow, (0, 0))
        
        # On ajoute les flèches
        window.blit(arrow_right, (arrow_right_x, arrow_y))
        window.blit(arrow_left, (arrow_left_x, arrow_y))

        # On ajoute le bouton jouer
        play.display()
        
        # On ajoute le texte
        title = font.getFont(window.height//8).render(game["config"]["name"], True, (255, 255, 255))
        window.blit(title, (window.width//2-title.width//2, min(140, window.height//6)-title.height//2))

        # On ajoute la description
        if description["game_index"] != game_idx or description["width"] != window.width:
            if description["game_index"] != game_idx:
                description["y"] = 40
            description["game_index"] = game_idx
            description["width"] = window.width
            description["surface"] = renderMultipleLines(font.getFont(window.height//30), window.width-80, game["config"]["description"]+"\n")
            shadow_size = (window.width-40, description["surface"].height+40)
            description["shadow"] = pygame.Surface(shadow_size, pygame.SRCALPHA)
            pygame.draw.rect(description["shadow"], (0, 0, 128), (0, 0, *shadow_size), border_radius=20)
        desc_surface = description["surface"]
        shadow = description["shadow"]
        shadow.set_alpha(min(round(description["y"]/desc_surface.height*120)+60, 255))
        window.blit(shadow, (window.width//2-shadow.width//2, window.height-description["y"]-20))
        window.blit(desc_surface, (window.width//2-desc_surface.width//2, window.height-description["y"]))

        # Si il y a une surface fantôme on l'affiche par dessus tout le reste
        if ghost_surface:
            window.blit(ghost_surface, (window.width//2-ghost_surface.width//2, window.height//2-ghost_surface.height//2))
            alpha = ghost_surface.get_alpha() - 10
            if alpha > 0:
                ghost_surface.set_alpha(alpha)
            else:
                ghost_surface = None
        
        pygame.display.flip()  # On actualise la fenêtre
        clock.tick(30)  # Limite la boucle à 30 itérations par seconde


def main() -> None:
    """
    La fonction main sert à démarrer tout le projet. Elle s'occupe de charger tous les mini-jeux 
    puis d'alterner entre le menu des mini-jeux et la phase de jeu.
    """
    
    FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script

    # Création de la fenêtre pygame
    
    pygame.init()
    pygame.mixer.init()  # Afin de jouer des sons plus tard

    window_size = (800, 600)
    window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption("Physics.play")

    # On charge les assets de base (icones et logo)
    assets = {}
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "preassets"))

    # On affiche une fenêtre de chargement
    pygame.display.set_icon(assets["images"]["icon.png"])
    window.fill((0, 0, 0))
    title = assets["images"]["title.png"]
    window.blit(title, (window_size[0]//2-title.width//2, window_size[1]//3-title.height//2))

    # On gère la barre de chargement
    loading = 0
    loading_bar_params = lambda: (loadingBar(400, 40, 6, loading / (3 if PRELOAD else 2)), (window_size[0]//2-200, window_size[1]//3*2-20))
    window.blit(*loading_bar_params())
    pygame.display.flip()
    
    # Chargement du reste des assets
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "assets"))
    loading = 1
    window.blit(*loading_bar_params())
    pygame.display.flip()
        
    # Chargement des mini-jeux
    
    games: list[dict] = []
    NEEDED_FILES = ("game.py", "config.json", "menu_background.png")  # Fichiers indispensables dans un dossier de mini-jeu
    print()

    # On scanne le dossier 'games' et on importe tous les mini-jeux qui remplissent les conditions
    scan = tuple(scandir(path.join(FOLDER_PATH, "games")))
    scan_lenght = len(scan)
    for element in scan:
        if element.is_dir():
            # Exception : on ne charge pas le mini-jeu 'template' qui sert d'exemple aux développeurs
            if element.name == "template":
                continue
            # On vérifie que tous les fichiers indispensables existent
            if all(path.exists(path.join(element.path, needed_file)) for needed_file in NEEDED_FILES):
                print("[Info] Dossier de mini-jeu détecté :", element.name)
                result = loadGame(element.name, FOLDER_PATH)
                if result == None:
                    print(f"[Erreur] Le dossier '{element.name}' n'a pas pu être chargé car il lui manquait des données. Merci de vérifier qu'il ne manque pas des clés au fichier 'config.json' et que le fichier 'game.py' possède les 4 fonctions principales (voir l'exemple 'template').")
                else:
                    games.append(result)
            else:
                print(f"[Erreur] Le dossier '{element.name}' ne contient pas tous les fichiers indispensables")
                print("[Rappel] les fichiers indispensables sont :", ", ".join(NEEDED_FILES))
        loading += 1 / scan_lenght
        window.blit(*loading_bar_params())
        pygame.display.flip()

    if len(games) == 0:
        print("[Erreur] Aucun jeu n'a été chargé : arrêt du programme")
        return
    
    if PRELOAD:
        games_lenght = len(games)
        for game in games:
            game["load"]()
            game["loaded"] = True
            loading += 1 / games_lenght
            window.blit(*loading_bar_params())
            pygame.display.flip()

    print("\nChargement des mini-jeux terminé :", len(games), "mini-jeu(x) chargé(s)")

    # On fait disparaitre graduellement la fenêtre de chargement
    ghost_surface = window.copy()
    ghost_surface.set_alpha(255)

    while True:
        
        user_choice = menu(games, window, assets, ghost_surface)  # On demande à l'utilisateur de choisir un mini-jeu
        if user_choice == None:
            break

        if ghost_surface:
            ghost_surface = None
        
        status = playGame(user_choice, window, assets)  # On fait tourner le mini-jeu et on récupère le status de sortie
        if status:
            break
    
    pygame.quit()  # On demande à pygame de tout fermer proprement


if __name__ == "__main__":
    main()

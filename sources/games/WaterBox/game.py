# Importation des librairies

import pygame
from os import path
from .sph_water import SPHSimulation, SPHParticle
from utils import loadAssetsFolder, RangeInput
import math

WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_SIZE = (1600, 900)
FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script

mouse_pos = {"x": 0, "y": 0}
cam_x = 0
cam_y = 0
event_list = []  # Liste des évènements
l_fps = -1 #fps du dernier tick
count = 0

#surface principale
surface = pygame.Surface(WINDOW_SIZE)

# Les sliders
viscosity : RangeInput = None
stiffness : RangeInput = None


# On initie les variables qui vont contenir les assets
background: pygame.Surface = None
container: pygame.Surface = None

# SPH Water Simulation
sph_sim: SPHSimulation = None

# On définit les 5 fonctions principales

def load() -> None:
    """
    load charge les assets.
    """
    global background, container

    assets = {}
    loadAssetsFolder(assets, path.join(FOLDER_PATH, "assets"))  # On utilise la fonction utilitaire loadAssetsFolder définie dans sources/utils.py

    background = assets["images"]["background.png"]
    container = assets["images"]["Container.png"]


    


def init() -> None:
    """
    Initialise/réinitialise le mini-jeu
    """
    
    global sph_sim, flow_x, step, count, viscosity, stiffness
    
    event_list.clear()
    # Initialise la simulation avec 20 particules en jet d'eau
    sph_sim = SPHSimulation(width=1600, height=800, particle_count=20)
    
    viscosity = RangeInput(1400, 30, 50, (0.01,0.9,0.01), surface, lambda value:f"Viscosité: {round(value,3)}", pygame.font.Font(), 4, sph_sim.viscosity)
    stiffness = RangeInput(1400, 60, 50, (1,200,1), surface, lambda value:f"Facteur de pression: {value}", pygame.font.Font(), 4, sph_sim.gas_stiffness)


i = 0

def tick(keys: dict, mouse: dict, fps:float) -> None:
    """
    Met à jour le jeu, execute un tick

    :param keys: Dictionnaire des touches pressées par l'utilisateur. Les valeurs correspondent à la durée de la pression de la touche. Exemple `{pygame.K_UP: 8, pygame.K_LEFT: 0, pygame.K_RIGHT: 1}`
    :type keys: dict
    :param mouse: Dictionnaire contenant les informations liées à la souris `{'x': int, 'y'; int, 'click': list[int, int, int]}`
    :type mouse: dict
    """
    global mouse_pos, cam_x, cam_y, sph_sim, l_fps, i, flow_x, world_x, world_y; viscosity, stiffness
    
    mouse_pos_interact = (-1000,-1000)

    #Tick les bouttons
    viscosity.tick((mouse["x"],mouse["y"]),mouse["click"][0])
    stiffness.tick((mouse["x"],mouse["y"]),mouse["click"][0])
    
    l_fps = fps
    
    """if i < count*3 and i%3 ==0 :
        for j in range(1,step+1):
            sph_sim.add_particle((flow_x[0]+i*SPHParticle().radius)+4,0)
        i += 1"""
    
    world_x = mouse["x"] + cam_x
    world_y = mouse["y"] + cam_y
    
    # Si le clic gauche de la souris est pressé, on compare sa position à la précédente pour faire déplacer la caméra
    if mouse["click"][0] > 0:
        cam_x += mouse_pos["x"] - mouse["x"]
        #cam_y += mouse_pos["y"] - mouse["y"]
        world_x = mouse["x"] + cam_x
        #world_y = mouse["y"] + cam_y
    
    if mouse["click"][1] > 0:
        if len(sph_sim.particles) < 600:
            if sph_sim and (0 < world_x < sph_sim.width and 0 < world_y < sph_sim.height):
                sph_sim.add_particle(world_x, world_y)
            
    if mouse["click"][2] > 0:
        mouse_pos_interact = (world_x, world_y-50)
        

    # Mis à jour de la position de la souris
    mouse_pos["x"], mouse_pos["y"] = mouse["x"], mouse["y"]

    # Option pour mettre en pause
    if keys[pygame.K_ESCAPE]:
        event_list.append({"type": "pause"})

    if i < 1000:
        sph_sim.step(dt=1/70, mouse=(-1,-1), viscosity=round(viscosity.value,3), stiffness=stiffness.value)  # timestep arbitraire
        i+=1
    
    # Met à jour la simulation
    if sph_sim:
        sph_sim.step(dt=(1/(fps+1)), mouse=mouse_pos_interact, viscosity=round(viscosity.value,3), stiffness=stiffness.value) # fps timestep
    
        
    


def display() -> pygame.Surface:
    """
    Rendu du jeu

    :return: L'affichage du mini-jeu
    :rtype: pygame.Surface
    
    """
    
    global background, container, surface, viscosity, stiffness
    
    
    

    surface.fill((76,232,255))
    
    
    
    
    #Afficher le background
    factor = math.ceil(WINDOW_SIZE[0] / background.size[0])
    
    for i in range(factor):
        surface.blit(background,(i*background.size[0],WINDOW_SIZE[1]-(background.size[0]/2)))
        
    surface.blit(container, (-20-cam_x,25))

    #Afficher les bouttons
    stiffness.display()
    viscosity.display()
    
    
    # Dessiner les particules d'eau
    if sph_sim:
        sph_sim.draw(surface, cam_x, -50)

        # Afficher les informations
        font = pygame.font.Font(None, 24)
        text = font.render(f"Particules: {sph_sim.get_particle_count()} (max 600)", True, (0, 0, 0))
        surface.blit(text, (10, 20))
        help_text = font.render("Cliquer et bouger pour se déplacer, clique molette ajoute des particules", True, (0, 0, 0))
        surface.blit(help_text, (10, 40))
        surface.blit(font.render("Clique droit vous permet d'interagir avec les particules", True, (0,0,0)), (10,60))
        
        global l_fps
        
        #afficher les fps
        surface.blit(font.render(f"FPS: {l_fps}", True, (0,0,0)), (10,80))

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
    
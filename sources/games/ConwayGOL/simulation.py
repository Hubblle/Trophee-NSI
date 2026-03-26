"""
Ce programme est une simulation du jeu de la vie de Conway.
Cette version utilise l'algorithme Hashlife pour compresser l'espace et le temps lors de la simulation.
Lien vers l'article utilisé pour implémenter le Hashlife : https://www.dev-mind.blog/hashlife

- Clic gauche pour changer l'état d'une cellule
- Espace pour lancer/arrêter la simulation
- Molette de souris ou défilement à 2 doigts pour zoomer/dézoomer
- Flèches directionnelles pour se déplacer sur la grille
- Shift + flèches pour aller plus vite
- Ctrl + Z durant pour revenir à l'état précédent de la grille
- Ctrl + X pour vider la grille
- Shift + sélectionner une zone avec la souris pour ajouter une structure au catalogue
- Ctrl + clic pour supprimer un élément du catalogue
"""

# Importation des librairies

import pygame
from math import floor, ceil
from os import path
from json import dump

pygame.init()  # Initiation de pygame
window_size = (1600, 900)
FOLDER_PATH = path.dirname(__file__)  # Chemin absolu du dossier contenant ce script

class RangeButton:  # Class du bouton de vitesse de simulation
    
    def __init__(self, y, button_range, set_target, get_target, offset_x, maxi):
        self.is_clicked = False
        self.range = button_range
        self.x = 0
        self.y = y
        self.set_target = set_target
        self.get_target = get_target
        self.offset_x = offset_x
        self.maxi = (lambda: maxi) if isinstance(maxi, int) else maxi
        
    def display(self):  # Affiche le bouton
        self.update()
        pygame.draw.circle(window, WHITE if self.is_clicked else LIGHT_GRAY, (self.x, self.y), 8)
        
    def update(self):
        if self.is_clicked:
            if mouse_data[0] > 0:
                self.set_target(max(1, min(self.maxi(), floor((mouse_data[1]-window_size[0]//2+self.range//2-self.offset_x)*(self.maxi()-1)/self.range+0.5)+1)))
            else:
                self.is_clicked = False
        self.x = window_size[0]//2-self.range//2+self.offset_x+round((self.get_target()-1)/(self.maxi()-1)*self.range)
        
    def onMouseClick(self, x, y):  # Clic de la souris
        if (self.x-x)**2+(self.y-y)**2 <= 64:
            self.is_clicked = True
            return True
        return False
    
    
class CatalogItem:  # Class représentant les structures du catalogue
    
    SIZE = 140
    PREVIEW_SIZE = 120
    INTERVAL = 16
    max_index = -1
    FONT = pygame.font.SysFont("arial", 18)
    catalog: list = None
    
    def __init__(self, index):
        self.index = index
        if index > CatalogItem.max_index:
            CatalogItem.max_index = index
        self.structure = CatalogItem.catalog[index]
        self.touching_mouse = False
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.preview = pygame.Surface((self.PREVIEW_SIZE, self.PREVIEW_SIZE), pygame.SRCALPHA)
        self.surface = None
        self.instant_paste = False
        self.tick()
        self.createSurface()
        self.createPreview()
        
    def tick(self):  # Mise à jour des coordonnées et vérification de la collision avec la souris
        item_per_line = (window_size[0]-self.INTERVAL-16) // (self.SIZE+self.INTERVAL)
        if (self.index // item_per_line) < (self.max_index // item_per_line):
            line_width = item_per_line * (self.SIZE+self.INTERVAL) - self.INTERVAL
        else:
            line_width = (self.max_index % item_per_line + 1) * (self.SIZE+self.INTERVAL) - self.INTERVAL
        x = (self.index % item_per_line) * (self.SIZE+self.INTERVAL) + window_size[0]//2 - line_width//2
        y = (self.index // item_per_line) * (self.SIZE+self.INTERVAL) + (window_size[1]-catalog_y) + self.INTERVAL
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.touching_mouse = self.rect.collidepoint(mouse_data[1], mouse_data[2])
        
    def display(self):  # Affichage
        color = ((180, 120, 135) if keys[pygame.K_LCTRL] else (185, 205, 225)) if self.touching_mouse else (175, 200, 230)
        pygame.draw.rect(window, color, self.rect, border_radius=10)
        window.blit(self.preview, (self.rect.x+(self.SIZE-self.PREVIEW_SIZE)//2, self.rect.y+(self.SIZE-self.PREVIEW_SIZE)//2))
        
    def createSurface(self):  # Création de la surface représentatant la structure
        if self.structure:
            x_axis, y_axis = tuple(zip(*self.structure))
            min_x_axis = min(x_axis)
            min_y_axis = min(y_axis)
            width = max(x_axis) - min_x_axis + 1
            height = max(y_axis) - min_y_axis + 1
        else:
            width, height = 0, 0
        if width*height > 10000:
            self.instant_paste = True
            if width*height > 10000000:
                width, height = 0, 0
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for x, y in self.structure:
            self.surface.set_at((x-min_x_axis, y-min_y_axis), BLACK)
        
    def createPreview(self):  # Création de l'aperçu à partir de la surface
        width, height = self.surface.get_size()
        if 0 < width and 0 < height:
            scale = min(self.PREVIEW_SIZE / width, self.PREVIEW_SIZE / height)
            scaled = pygame.transform.scale_by(self.surface, scale)
            size = scaled.get_size()
            self.preview.blit(scaled, (self.PREVIEW_SIZE//2-size[0]//2, self.PREVIEW_SIZE//2-size[1]//2))
        else:
            txt = self.FONT.render("Aucun aperçu", True, (100, 125, 145))
            txt_size = txt.get_size()
            self.preview.blit(txt, (self.PREVIEW_SIZE//2-txt_size[0]//2, self.PREVIEW_SIZE//2-txt_size[1]//2))

            
class Node:
    
    __slots__ = ('depth', 'a', 'b', 'c', 'd', 'result', 'hash', 'n')
    
    def __init__(self, depth, a, b, c, d):
        self.depth = depth
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.n = (a.n + b.n + c.n + d.n) if self.depth > 1 else (a + b + c + d)
        self.result = [None] * (self.depth - 1)
        self.hash = hash((id(self.a), id(self.b), id(self.c), id(self.d)))
            
    def evolve(self):  # Fonction de simulation utilisant l'algorithme Hashlife pour compresser l'espace et le temps
        
        # Si la node a déjà été calculée au moins 1 fois, on réutilise le résultat enregistré
        self_temporal_compression = min(temporal_compression_level, len(self.result)-1)
        result = self.result[self_temporal_compression]
        if result == None:
            if self.n == 0:
                result = getEmptyNode(self.depth-1)
            elif self.depth == 2:  # Simulation classique pour les plus petites nodes (4x4)
                an = self.a.a + self.a.b + self.a.c + self.b.a + self.b.c + self.c.a + self.c.b + self.d.a
                bn = self.a.b + self.b.a + self.a.d + self.c.b + self.d.a + self.b.b + self.b.d + self.d.b
                cn = self.a.c + self.a.d + self.b.c + self.c.a + self.c.c + self.c.d + self.d.a + self.d.c
                dn = self.a.d + self.b.c + self.b.d + self.c.b + self.c.d + self.d.b + self.d.c + self.d.d
                a = 1 < an < 4 if self.a.d else an == 3
                b = 1 < bn < 4 if self.b.c else bn == 3
                c = 1 < cn < 4 if self.c.b else cn == 3
                d = 1 < dn < 4 if self.d.a else dn == 3
                result = newNode(1, a, b, c, d)
            else:
                node1 = self.a
                node2 = newNode(self.depth-1, self.a.b, self.b.a, self.a.d, self.b.c)
                node3 = self.b
                node4 = newNode(self.depth-1, self.a.c, self.a.d, self.c.a, self.c.b)
                node5 = self.getCenterNode()
                node6 = newNode(self.depth-1, self.b.c, self.b.d, self.d.a, self.d.b)
                node7 = self.c
                node8 = newNode(self.depth-1, self.c.b, self.d.a, self.c.d, self.d.c)
                node9 = self.d
                
                node1Res = node1.evolve()
                node2Res = node2.evolve()
                node3Res = node3.evolve()
                node4Res = node4.evolve()
                node5Res = node5.evolve()
                node6Res = node6.evolve()
                node7Res = node7.evolve()
                node8Res = node8.evolve()
                node9Res = node9.evolve()
                
                intermediateNode1 = newNode(self.depth-1, node1Res, node2Res, node4Res, node5Res)
                intermediateNode2 = newNode(self.depth-1, node2Res, node3Res, node5Res, node6Res)
                intermediateNode3 = newNode(self.depth-1, node4Res, node5Res, node7Res, node8Res)
                intermediateNode4 = newNode(self.depth-1, node5Res, node6Res, node8Res, node9Res)
                
                if (self.depth-3 < temporal_compression_level or temporal_compression_level == -1) and self is not root:
                    result = newNode(self.depth-1,
                                intermediateNode1.evolve(),
                                intermediateNode2.evolve(),
                                intermediateNode3.evolve(),
                                intermediateNode4.evolve()
                                )
                else:
                    result = newNode(self.depth-1,
                                intermediateNode1.getCenterNode(),
                                intermediateNode2.getCenterNode(),
                                intermediateNode3.getCenterNode(),
                                intermediateNode4.getCenterNode()
                                )
            self.result[self_temporal_compression] = result
        return result
        
    def getCenterNode(self):  # Retourne la node centrale de celle-ci, centrée et 2 fois plus petite
        return newNode(self.depth-1, self.a.d, self.b.c, self.c.b, self.d.a)
    
    def getSubNodes(self):  # Retourne la position relative de chaque sous-node et celle-ci
        half = 2**(self.depth-1)
        yield 0, 0, self.a
        yield half, 0, self.b
        yield 0, half, self.c
        yield half, half, self.d
        
    def getSubNodeFromXY(self, dx, dy):  # Retourne la sous-node correspondante à dx, dy
        match dx, dy:
            case 0, 0: return self.a
            case 1, 0: return self.b
            case 0, 1: return self.c
            case 1, 1: return self.d
        raise ValueError
        
    def setCell(self, x, y, cx, cy, value):  # Renvoie une nouvelle node de la même taille avec la cellule modifiée
        
        cached = edit_cache.get((self, cx-x, cy-y, value))
        if cached != None:
            return cached
        
        if self.depth == 1:
            result = newNode(1, *(value if x+dx == cx and y+dy == cy else cell for dx, dy, cell in self.getSubNodes()))
            edit_cache[(self, cx-x, cy-y, value)] = result
            return result

        half = 2**(self.depth-1)
        result = newNode(self.depth, *(node.setCell(x+dx, y+dy, cx, cy, value)
                                     if x+dx <= cx < x+dx+half and y+dy <= cy < y+dy+half else node
                                     for dx, dy, node in self.getSubNodes()
                                     )
                       )
        edit_cache[(self, cx-x, cy-y, value)] = result
        return result
    
    def isLiving(self, x, y, cx, cy):  # Retourne True si la cellule en cx, cy est vivante sinon False
        if self.n == 0:
            return False
        if self.depth == 1:
            return self.getSubNodeFromXY(cx-x, cy-y)
        half = 2**(self.depth-1)
        for dx, dy, node in self.getSubNodes():
            if x+dx <= cx < x+dx+half and y+dy <= cy < y+dy+half:
                return node.isLiving(x+dx, y+dy, cx, cy)
        return False
    
    def display(self, x, y, bx, by, window_rect):  # Affichage de la node
        if self.n == 0: return
        size = 2**self.depth
        if not window_rect.colliderect(x*size+root_x, y*size+root_y, size, size): return
        if self.depth == 1 and min_depth_display == 0:
            for dx, dy, cell in self.getSubNodes():
                if cell:
                    pygame.draw.rect(window, BLACK, ((2*x+dx)*displayed_node_size+bx, (2*y+dy)*displayed_node_size+by, displayed_node_size, displayed_node_size))
        elif self.depth <= min_depth_display:
            p = self.n / 2**self.depth
            c = 0 if p > 0.8 else floor(255 - 255 * p / 0.8)
            if c < 255:
                pygame.draw.rect(window, (c,)*3, (x*displayed_node_size+bx, y*displayed_node_size+by, displayed_node_size, displayed_node_size))
        else:
            for dx, dy, node in self.getSubNodes():
                node.display(2*x+min(dx, 1), 2*y+min(dy, 1), bx, by, window_rect)
        
    def __hash__(self):
        return self.hash
    
    def __eq__(self, node):
        if not isinstance(node, Node): return False
        return id(self.a) == id(node.a) and id(self.b) == id(node.b) and id(self.c) == id(node.c) and id(self.d) == id(node.d)

    def __ne__(self, node):
        return not self.__eq__(node)
    
    def __repr__(self):
        if self.depth == 1:
            return f"Node 2x2 a={self.a} b={self.b} c={self.c} d={self.d}"
        return f"Node {2**self.depth}x{2**self.depth} depth={self.depth} n={self.n}"
             

# Définition des fonctions

def newNode(depth, a, b, c, d):  # Vérifie si une node avec les mêmes propriétés existe et la retourne, sinon en créé une nouvelle
    key = (a, b, c, d)
    node = known_nodes.get(key)
    if node == None:
        node = Node(depth, a, b, c, d)
        known_nodes[key] = node
    return node


def updateRootSize():  # Met à jour la taille de la node racine
    while any(node.n > 0 for node in (
        root.a.d.a, root.a.d.b, root.a.d.c,
        root.b.c.a, root.b.c.b, root.b.c.d,
        root.c.b.a, root.c.b.c, root.c.b.d,
        root.d.a.b, root.d.a.c, root.d.a.d,
        root.a.a, root.a.b, root.a.c,
        root.b.a, root.b.b, root.b.d,
        root.c.a, root.c.c, root.c.d,
        root.d.b, root.d.c, root.d.d)):
        increaseRootSize()
    
    
def increaseRootSize():  # Augmente la profondeur (et donc la taille) de la racine de 1
    global root, root_depth, root_x, root_y
    root_depth += 1
    empty_node = getEmptyNode(root_depth-2)
    root = newNode(root_depth,
                newNode(root_depth-1, empty_node, empty_node, empty_node, root.a),
                newNode(root_depth-1, empty_node, empty_node, root.b, empty_node),
                newNode(root_depth-1, empty_node, root.c, empty_node, empty_node),
                newNode(root_depth-1, root.d, empty_node, empty_node, empty_node)
                )
    root_x = - 2**(root_depth-1)
    root_y = root_x


def simulateCells():  # Simule les cellules à partir de la node racine
    global root
    updateRootSize()
    new_root = root.evolve()
    root = newNode(root.depth,
                   newNode(root.depth-1, root.a.a, root.a.b, root.a.c, new_root.a),
                   newNode(root.depth-1, root.b.a, root.b.b, new_root.b, root.b.d),
                   newNode(root.depth-1, root.c.a, new_root.c, root.c.c, root.c.d),
                   newNode(root.depth-1, new_root.d, root.d.b, root.d.c, root.d.d)
    )
        

def displayCells():  # Affiche les cellules
    bx = window_size[0]//2-scroll_x
    by = window_size[1]//2-scroll_y
    half = 2**(root_depth-min_depth_display-1) * displayed_node_size
    cell_size = displayed_node_size / 2**min_depth_display
    window_rect = pygame.Rect(floor(-bx/cell_size), floor(-by/cell_size), ceil(window_size[0]/cell_size)+1, ceil(window_size[1]/cell_size)+1)
    root.display(0, 0, bx-half, by-half, window_rect)
    
    
def onMouseClick(nb_clicks, x, y):  # Clic de souris
    global brush, opening_catalog, copied_item, copy_rect, save_catalog
    if nb_clicks == 1 and (speed_button.onMouseClick(x, y) or clearness_button.onMouseClick(x, y) or temporal_button.onMouseClick(x, y)):
        return
    if nb_clicks > 0:
        1
    if simulating: return
    if opening_catalog:
        if mouse_data[0] == 1 and mouse_data[2] < window_size[1]-16-catalog_y:
            opening_catalog = False
        elif mouse_data[0] == 1 and catalog_y > window_size[1]-165:
            for i in range(len(catalog_items)):
                catalog_item = catalog_items[i]
                if catalog_item.touching_mouse:
                    if keys[pygame.K_LCTRL]:
                        index = catalog_items.pop(i).index
                        CatalogItem.catalog.pop(index)
                        CatalogItem.max_index -= 1
                        for catalog_item_ in catalog_items:
                            if catalog_item_.index > index:
                                catalog_item_.index -= 1
                        save_catalog = True
                    else:
                        if catalog_item.instant_paste:
                            w, h = catalog_item.surface.get_size()
                            i = floor(scroll_y / (displayed_node_size / 2**min_depth_display))
                            j = floor(scroll_x / (displayed_node_size / 2**min_depth_display))
                            pasteCatalogItem(catalog_item.index, j-w//2, i-h//2)
                        else:
                            copied_item = catalog_item
                        opening_catalog = False
                    return
        return
    elif mouse_data[0] == 1 and mouse_data[2] >= window_size[1]-16:
        opening_catalog = True
        return
    i = floor((y+scroll_y-window_size[1]//2) / (displayed_node_size / 2**min_depth_display))
    j = floor((x+scroll_x-window_size[0]//2) / (displayed_node_size / 2**min_depth_display))
    if copied_item:
        if nb_clicks == 1:
            w, h = copied_item.surface.get_size()
            pasteCatalogItem(copied_item.index, j-w//2, i-h//2)
            if keys[pygame.K_LSHIFT] == 0:
                copied_item = None
        return
    if nb_clicks == 1:
        if keys[pygame.K_LSHIFT] > 0:
            copy_rect = [j, i, 0, 0]
        else:
            brush = root.isLiving(root_x, root_y, j, i)
    elif copy_rect:
        copy_rect[2] = j-copy_rect[0]
        copy_rect[3] = i-copy_rect[1]
    if brush == None: return
    setCell(j, i, not brush)
        

def displayStats():  # Affiche le bandeau de statistique en haut de l'écran
    pygame.draw.rect(window, BLACK, (window_size[0]//2-400, -40, 800, 110), border_radius=40)
    txt = font.render(f"Vitesse de simulation : {simulation_speed} ticks/s", True, WHITE)
    txt_size = txt.get_size()
    window.blit(txt, (window_size[0]//2-txt_size[0]//2-250, 20-txt_size[1]//2))
    pygame.draw.rect(window, LIGHT_GRAY, (window_size[0]//2-340, 40, 180, 5), border_radius=2)
    speed_button.display()
    txt = font.render(f"Compression temporelle : {2**temporal_compression_level} gen/tick", True, WHITE)
    txt_size = txt.get_size()
    window.blit(txt, (window_size[0]//2-txt_size[0]//2+250, 20-txt_size[1]//2))
    pygame.draw.rect(window, LIGHT_GRAY, (window_size[0]//2+160, 40, 180, 5), border_radius=2)
    temporal_button.display()
    txt = font.render(f"Netteté : {clearness} %", True, WHITE)
    txt_size = txt.get_size()
    window.blit(txt, (window_size[0]//2-txt_size[0]//2, 20-txt_size[1]//2))
    pygame.draw.rect(window, LIGHT_GRAY, (window_size[0]//2-80, 40, 160, 5), border_radius=2)
    clearness_button.display()
    

def setCell(x, y, value, check_size=True):  # Affecte une valeur à une cellule
    global root
    if check_size:
        maxi = max(abs(x), abs(y))
        while maxi > 2**(root_depth-3):
            increaseRootSize()
    root = root.setCell(root_x, root_y, x, y, value)
    
def changeCellSize(value):  # Zoom / Dezoom
    global zoom, scroll_x, scroll_y
    real_scroll_x = scroll_x / displayed_node_size
    real_scroll_y = scroll_y / displayed_node_size
    zoom = value
    updateDisplayedNodeSize()
    scroll_x = round(real_scroll_x*displayed_node_size)
    scroll_y = round(real_scroll_y*displayed_node_size)
    
    
def updateCatalog():  # Actualise la position du catalogue
    global catalog_y
    if opening_catalog:
        catalog_y += (window_size[1]-160-catalog_y) // 4
    else:
        if 0 < catalog_y < 4:
            catalog_y -= 1
        else:
            catalog_y -= catalog_y // 4
            
    if catalog_y > 0:
        for catalog_item in catalog_items:
            catalog_item.tick()


def displayCatalog():  # Affiche le catalogue
    if catalog_y > 0:
        pygame.draw.rect(window, (140, 170, 220), (0, window_size[1]-16-catalog_y, window_size[0], catalog_y+32), border_radius=16)
        pygame.draw.rect(window, (160, 190, 225), (8, window_size[1]-catalog_y, window_size[0]-16, catalog_y+16), border_radius=16)
        for catalog_item in catalog_items:
            catalog_item.display()
    else:
        if mouse_data[2] < window_size[1]-16:
            color = (140, 170, 220)
        else:
            color = (155, 180, 225)
        pygame.draw.rect(window, color, (0, window_size[1]-16, window_size[0], 32), border_radius=16)
        

def pasteCatalogItem(index, x, y):  # Colle un élément du catalogue sur la grille
    structure = CatalogItem.catalog[index]
    if not structure:
        return
    x_axis, y_axis = tuple(zip(*structure))
    min_x_axis = min(x_axis)
    min_y_axis = min(y_axis)
    max_x = max(abs(cell_x+x-min_x_axis) for cell_x, _ in structure)
    max_y = max(abs(cell_y+y-min_y_axis) for _, cell_y in structure)
    setCell(max_x, max_y, False)
    for cell_x, cell_y in structure:
        setCell(cell_x+x-min_x_axis, cell_y+y-min_y_axis, True, False)
    edit_cache.clear()
        

def displayCopiedItem():  # Affiche la structure copiée du catalogue
    if copied_item:
        cell_size = displayed_node_size / 2**min_depth_display
        surface = pygame.transform.scale_by(copied_item.surface, floor(cell_size))
        surface.set_alpha(160)
        w, h = copied_item.surface.get_size()
        x = floor((floor((mouse_data[1]+scroll_x-window_size[0]//2) / cell_size) - w//2) * cell_size) - scroll_x + window_size[0]//2
        y = floor((floor((mouse_data[2]+scroll_y-window_size[1]//2) / cell_size) - h//2) * cell_size) - scroll_y + window_size[1]//2
        window.blit(surface, (x, y))
        

def absRect(rect):  # Retourne le rectangle avec une taille positive
    rect = rect.copy()
    if rect[2] < 0:
        rect[0] += rect[2]
        rect[2] = -rect[2]
    if rect[3] < 0:
        rect[1] += rect[3]
        rect[3] = -rect[3]
    return rect
        
        
def addToCatalog(copy_rect):  # Ajoute la zone sélectionnée au catalogue
    global save_catalog
    save_catalog = True
    rect = absRect(copy_rect)
    cells = [[x-rect[0], y-rect[1]] for x in range(rect[0], rect[0]+rect[2]+1) for y in range(rect[1], rect[1]+rect[3]+1) if root.isLiving(root_x, root_y, x, y)]
    CatalogItem.catalog.append(cells)
    catalog_items.append(CatalogItem(len(CatalogItem.catalog)-1))
    
    
def displayCopyRect():  # Affiche le rectangle de sélection
    rect = absRect(copy_rect)
    cell_size = displayed_node_size / 2**min_depth_display
    surface = pygame.Surface((floor((rect[2]+1)*cell_size), floor((rect[3]+1)*cell_size)), pygame.SRCALPHA)
    surface.fill(GREEN)
    surface.set_alpha(120)
    window.blit(surface, (window_size[0]//2-scroll_x+floor(rect[0]*cell_size), window_size[1]//2-scroll_y+floor(rect[1]*cell_size)))
    
    
def getEmptyNode(depth):  # Retourne une node avec la profondeur demandée
    while depth > len(empty_nodes):
        empty_nodes.append(newNode(len(empty_nodes)+1, *[empty_nodes[-1]]*4))
    return empty_nodes[depth-1]


def updateDisplayedNodeSize():  # Met à jour displayed_node_size à partir du zoom et du niveau de netteté
    global displayed_node_size, min_depth_display
    min_depth_display = floor((1-clearness/100) * (root_depth+1))
    displayed_node_size = floor(2**min_depth_display * zoom)
    while displayed_node_size < 1:
        min_depth_display += 1
        displayed_node_size = floor(2**min_depth_display * zoom)
    
    
def setSimulationSpeed(v):
    global simulation_speed
    simulation_speed = v
    

def setClearness(v):
    global clearness
    clearness = v
    updateDisplayedNodeSize()
    
    
def setTemporalCompressionLevel(v):
    global temporal_compression_level
    temporal_compression_level = v-1


def reset() -> None:
    """
    Reset la grille.
    """
    global root_depth, root, temporal_compression_level, simulating, scroll_x, scroll_y
    root_depth = 4
    root = getEmptyNode(root_depth)
    temporal_compression_level = min(temporal_compression_level, 3)
    simulating = False
    scroll_y = scroll_x = 0


def simulate(keys_: dict, mouse: tuple, wheel: int):
    global opening_catalog, catalog_y, copied_item, window_size, init_simulation, scroll_x, scroll_y, last_matrix, keys, mouse_data, \
        main_loop_ticks, copy_rect, brush, simulating, root, root_depth, temporal_compression_level, simulation_loop_ticks, save_catalog
    
    if wheel != 0:
        changeCellSize(zoom * 1.1**wheel)

    # Boucle de simulation

    if simulating:
        simulation_loop_ticks += 1
        if simulation_loop_ticks >= MAX_SPEED / simulation_speed:
            simulation_loop_ticks -= MAX_SPEED / simulation_speed
            simulateCells()
    
    # Boucle principale

    main_loop_ticks += 1
    if main_loop_ticks >= MAX_SPEED / LOOP_SPEED:
        main_loop_ticks -= MAX_SPEED / LOOP_SPEED

        for key in keys_:
            if keys_[key] > 0:
                if key in keys:
                    keys[key] += 1
            else:
                keys[key] = 0
                    
        # Mise à jour des données
        
        if keys[pygame.K_z] == 1 and keys[pygame.K_LCTRL] > 0 and last_matrix:
            simulating = False
            root = last_matrix
            
        if keys[pygame.K_x] == 1 and keys[pygame.K_LCTRL] > 0:
            reset()
            
        if keys[pygame.K_c] == 1 and keys[pygame.K_LCTRL] > 0:
            edit_cache.clear()

        if keys[pygame.K_SPACE] == 1:
            simulating = not simulating
            if simulating:
                last_matrix = root
                opening_catalog = False
                catalog_y = 0
                copied_item = None
                copy_rect = None
                init_simulation = True

        scroll_x += ((keys[pygame.K_RIGHT] > 0) - (keys[pygame.K_LEFT] > 0)) * (30 if keys[pygame.K_LSHIFT] > 0 else 14)
        scroll_y += ((keys[pygame.K_UP] > 0) - (keys[pygame.K_DOWN] > 0)) * (-30 if keys[pygame.K_LSHIFT] > 0 else -14)
                    
        mouse_data[1], mouse_data[2] = mouse[1], mouse[2]
        if mouse[0]:
            mouse_data[0] += 1
        else:
            mouse_data[0] = 0
        
        if mouse_data[0] > 0:
            onMouseClick(*mouse_data)
        else:
            brush = None
            if copy_rect:
                addToCatalog(copy_rect)
                copy_rect = None
            
        speed_button.update()
        clearness_button.update()
        temporal_button.update()
        updateCatalog()
    
    if save_catalog:
        save_catalog = False
        with open(path.join(FOLDER_PATH, "assets", "json", "catalog.json"), "w") as f:
            dump(CatalogItem.catalog, f, indent=2)


def render(surface: pygame.Surface):
    global window
    window = surface

    # Affichage
        
    window.fill(WHITE)  # Efface l'écran
    
    displayCells()
    if copy_rect and not simulating:
        displayCopyRect()    
    displayCopiedItem()
    displayStats()
    if not simulating:
        displayCatalog()


# Définition des couleurs

WHITE = (255, 255, 255)
LIGHT_GRAY = (220, 220, 220)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Création de l'arborescence des noeuds et cellules

edit_cache = {}
known_nodes = {}
empty_nodes = [newNode(1, False, False, False, False)]
root_depth = 4
root = getEmptyNode(root_depth)
root_x = -(2**(root_depth-1))
root_y = -(2**(root_depth-1))

font = pygame.font.SysFont("arial", 16)
window: pygame.Surface = None
keys = {}

zoom = 40
displayed_node_size = zoom
min_depth_display = 0
clearness = 100
temporal_compression_level = 0
simulating = False
simulation_speed = 5
MAX_SPEED = 100
speed_button = RangeButton(42, 180, setSimulationSpeed, lambda: simulation_speed, -250, MAX_SPEED)
clearness_button = RangeButton(42, 160, setClearness, lambda: clearness, 0, 100)
temporal_button = RangeButton(42, 180, setTemporalCompressionLevel, lambda: temporal_compression_level+1, 250, lambda: root_depth)
mouse_data = [0, 0, 0]  # Informations sur la souris : [durée du clic, x, y]
LOOP_SPEED = 24
simulation_loop_ticks = 0
main_loop_ticks = 0
scroll_x = 0
scroll_y = 0
brush = None
last_matrix = None
catalog_y = 0
opening_catalog = False
catalog_items = []
copied_item = None
copy_rect = None
save_catalog = False


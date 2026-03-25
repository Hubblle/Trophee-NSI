from math import sin, cos, sqrt, atan, pi
from typing import Self, Callable
from pygame import Surface, transform
from utils import SpriteSheet

def getDirection(dx: float, dy: float) -> float:
    """
    Retourne une direction correspondant à celle d'un vecteur 2D dont les coordonnées sont dx et dy.

    :param dx: Coordonnée/mouvement x
    :type dx: float
    :param dy: Coordonnée/mouvement y
    :type dy: float
    :return: Une direction
    :rtype: rad
    """
    if dx == 0:
        return pi/2 if dy > 0 else -pi/2
    direction = atan(dy / dx)
    if dx < 0:
        if direction > 0:
            direction -= pi
        else:
            direction += pi
    return direction


def absModulo(value: float, modulo: float) -> float:
    """
    Retourne le modulo de la valeur absolue de value en gardant le signe de value.

    :param value: La valeur à moduler
    :type value: float
    :param modulo: Le modulo
    :type modulo: float
    :return: Le modulo de la valeur absolue de value en gardant le signe de value
    :rtype: float
    """
    return (abs(value) % modulo) * (1 if value >= 0 else -1)

class Vector:

    def __init__(self, coordinates: tuple = None, magnitude: float = None, direction: float = None):
        """
        Retourne un objet représentant un vecteur 2D soit à partir de sa direction et norme, soit à partir de ses coordonnées. 
        Si les 2 informations sont données, les coordonnées sont prioritaires. 
        Si aucune n'est donné, un vecteur nul est retourné.

        :param coordinates: Coordonnées du vecteur
        :type coordinates: tuple[float, float]
        :param magnitude: Norme du vecteur, va de pair avec la direction
        :type magnitude: float
        :param direction: Direction du vecteur (rad), va de pair avec la norme
        :type direction: float
        """
        self._magnitude = magnitude
        self.direction = direction
        if coordinates:
            self.coordinates = coordinates
        if not (self.magnitude != None and self.direction != None):
            self.magnitude = 0
            self.direction = 0

    @property
    def magnitude(self) -> float:
        return self._magnitude
    
    @magnitude.setter
    def magnitude(self, v: float) -> None:
        # Pour éviter une norme négative, on utilise une valeur absolue et on retourne la direction si besoin
        self._magnitude = abs(v)
        if v < 0:
            self.direction += pi if self.direction <= 0 else -pi
    
    @property
    def x(self) -> float:
        return self._magnitude * cos(self.direction)
    
    @property
    def y(self) -> float:
        return self._magnitude * sin(self.direction)
    
    @property
    def coordinates(self) -> tuple:
        return self.x, self.y
    
    @coordinates.setter
    def coordinates(self, xy: tuple | list):
        self.direction = getDirection(*xy)
        self._magnitude = sqrt(xy[0]**2 + xy[1]**2)
    
    def sum(self, *vectors: Self) -> Self:
        """
        Fait la somme du vecteur self et de tous les autres vecteurs passés en paramètre à la suite 
        et renvoie un nouvel objet Vector.

        :param vectors: Les vecteurs à additionner
        :type vectors: Vector
        :return: Un nouvel objet Vector
        :rtype: Vector
        """
        sum_x = self.x + sum(vector.x for vector in vectors)
        sum_y = self.y + sum(vector.y for vector in vectors)
        return Vector((sum_x, sum_y))
    
    def __add__(self, other: Self) -> Self:
        # Méthode spéciale (appelée dunder method) qui permet d'additioner des objets
        return self.sum(other)

    def __mul__(self, product: float) -> Self:
        # Dunder qui permet de multiplier un objet par un nombre
        return Vector((self.x*product, self.y*product))

    def __rmul__(self, product: float) -> Self:
        return self.__mul__(product)
        

class CelestialBody:
    """
    Cette class représente un astre et permet de calculer les forces qui s'exercent sur celui-ci 
    et d'en déduire son accélération ainsi que sa vitesse en utilisant la 2e loi de Newton et le 
    calcul de la force gravitationelle.
    """

    def __init__(self, x: int, y: int, mass: float, radius: int, black_hole: bool = False):
        """
        :param x: Abscisse de l'astre (en m)
        :type x: int
        :param y: Ordonnée de l'astre (en m)
        :type y: int
        :param mass: Masse de l'astre (en kg)
        :type mass: float
        :param radius: Rayon de l'astre (en m)
        :type radius: int
        :param black_hole: Si l'astre est un trou noir, on modifie la formule du calcul des forces gravitationnelles pour qu'il n'attire que les astres proches de lui
        :type black_hole: bool
        """
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.other_bodies = []
        self.acceleration = Vector()  # Vecteur accélération en m/s^2
        self.speed = Vector()  # Vecteur vitesse en m/s
        self.locked = False
        self.is_black_hole = black_hole
    
    def stop(self) -> None:
        """
        Remet à zéro la vitesse et l'accélération de l'astre.
        """
        self.acceleration.magnitude = 0
        self.speed.magnitude = 0
    
    def collide(self, body: Self) -> bool:
        """
        Retourne True si cet astre est en collision avec body.

        :param body: L'astre avec lequel on veut tester la collision
        :type body: CelestialBody
        :return: True si les 2 astres sont en collision, False sinon
        :rtype: bool
        """
        dx = self.x - body.x
        dy = self.y - body.y
        distance = sqrt(dx**2 + dy**2)
        return distance < self.radius + body.radius
    
    def addInteraction(self, body: Self) -> None:
        self.other_bodies.append(body)
    
    def getVector(self, body: Self) -> Vector:
        """
        Retourne le vecteur reliant cet astre et body.

        :param body: L'astre avec lequel on veut calculer le vecteur
        :type body: CelestialBody
        :return: Le vecteur reliant les 2 astres (en m)
        :rtype: Vector
        """
        dx = body.x - self.x
        dy = body.y - self.y
        return Vector((dx, dy))
    
    def calculateForce(self, body: Self) -> Vector:
        """
        Retourne le vecteur force gravitationnelle que body exerce sur cet astre.

        :param body: L'astre qui exerce la force gravitationnelle sur cet astre
        :type body: CelestialBody
        """
        # On utilise le calcul de la force gravitationnelle : F = G * m1 * m2 / d^2
        vector = self.getVector(body)
        value = 6.6743e-11 * self.mass * body.mass / vector.magnitude**(3 if body.is_black_hole else 2)
        return Vector(magnitude=value, direction=vector.direction)
    
    def calculateForces(self, bodies: tuple | list) -> Vector:
        """
        Retourne la somme des forces s'exerçant sur cet astre à partir de 
        la liste d'astres bodies.

        :param bodies: Les astres intéragissant avec celui-ci
        :type bodies: tuple[CelestialBody] | list[celestialBody]
        :return: Un vecteur force
        :rtype: Vector
        """
        if len(bodies) == 0:
            return Vector()  # Vecteur nul
        # On calcule la force que chaque astre dans bodies exerce sur cet astre et on fait la somme
        return Vector.sum(*(self.calculateForce(body) for body in bodies))
    
    def calculateAcceleration(self) -> None:
        sum_forces = self.calculateForces(self.other_bodies)
        # D'après la 2e loi de Newton : l'accélération est le quotient de la somme des forces par la masse
        # De plus le vecteur de la somme des forces a la même direction que le vecteur accélération
        self.acceleration.direction = sum_forces.direction
        self.acceleration.magnitude = sum_forces.magnitude / self.mass
    
    def calculateMovement(self, dt: float) -> Vector:
        """
        Calcule la variation de position de l'astre à partir de sa vitesse et du temps écoulé depuis le dernier appel de la fonction.

        :param dt: Temps écoulé entre chaque appel de la fonction (s)
        :type dt: float
        :return: La variation de position de l'astre (en m)
        :rtype: Vector
        """
        # Le vecteur déplacement est le produit du vecteur vitesse et du temps
        return self.speed * dt
    
    def move(self, dt: float, time_scale: int) -> None:
        """
        Calcule les forces s'exerçant sur l'astre, son accélération et sa vitesse puis actualise sa position.

        :param dt: Temps écoulé entre chaque appel de la fonction (s)
        :type dt: float
        :param time_scale: Échelle du temps (1s de jeu correspond à time_scale secondes réelles)
        :type time_scale: int
        """
        if self.locked:
            return
        self.calculateAcceleration()
        # Le vecteur variation de vitesse est le produit du vecteur accélération et du temps
        speed_variation = self.acceleration * dt * time_scale
        # Le vecteur vitesse actuelle est la somme du vecteur vitesse précédent et du vecteur variation de vitesse
        self.speed += speed_variation
        # On actualise la position à partir de la vitesse et du temps écoulé depuis le dernier appel de la fonction
        movement = self.calculateMovement(dt * time_scale)
        self.x += movement.x
        self.y += movement.y


class GraphicalCelestialBody(CelestialBody):

    def __init__(self, x: int, y: int, mass: float, radius: int, image: Surface | SpriteSheet, surface: Surface, getPosition: Callable[[int, int], tuple[int, int]], black_hole: bool = False):
        """
        Class héritant de CelestialBody et ajoutant des propriétés graphiques pour le rendu de l'astre.

        :param x: Abscisse de l'astre (en m)
        :type x: int
        :param y: Ordonnée de l'astre (en m)
        :type y: int
        :param mass: Masse de l'astre (en kg)
        :type mass: float
        :param radius: Rayon de l'astre (en m)
        :type radius: int
        :param image: Image de l'astre pour le rendu (peut être animée)
        :type image: pygame.Surface | utils.SpriteSheet
        :param surface: Surface sur laquelle afficher l'astre
        :type surface: pygame.Surface
        :param getPosition: Fonction permettant de convertir les coordonnées absolues (en m) en coordonnées relatives à l'écran (en px)
        :type getPosition: Callable[[int, int], tuple[int, int]]
        :param black_hole: Si l'astre est un trou noir, on modifie la formule du calcul des forces gravitationnelles pour qu'il n'attire que les astres proches de lui
        :type black_hole: bool
        """
        super().__init__(x, y, mass, radius, black_hole)
        self.original_image = image
        self.animated = isinstance(image, SpriteSheet)
        # Dictionnaire d'images de différentes tailles pour l'adaptation au zoom
        self.images: dict[int, Surface | list[Surface]] = {}
        self.angle = 0  # Angle de rotation de l'image en degrés
        self.surface = surface
        self.getPosition = getPosition
    
    def display(self, scale: int) -> None:
        """
        Affiche l'astre à sa position actuelle en prenant en compte la rotation de son image.

        :param scale: Échelle du rendu (en m/px)
        :type scale: int
        """
        x, y = self.getPosition(self.x, self.y)
        if self.animated:
            if scale in self.images:
                images = self.images[scale]
            else:
                images = [None] * len(self.original_image.frames)
                self.images[scale] = images
            current_frame = self.original_image.getCurrentSprite()
            frame = self.original_image.frame
            image = images[frame]
            if image is None:
                image = transform.scale_by(current_frame, self.radius*2 / scale / current_frame.width)
                images[frame] = image
        else:
            if scale in self.images:
                image = self.images[scale]
            else:
                image = transform.scale_by(self.original_image, self.radius*2 / scale / self.original_image.width)
                self.images[scale] = image
        if self.angle != 0:
            image = transform.rotate(image, self.angle)
        self.surface.blit(image, (x - image.width//2, y - image.height//2))
    
    def isTouchingMouse(self, mouse_x: int, mouse_y: int, scale: int) -> bool:
        """
        Retourne True si la souris touche l'astre sinon False.

        :param mouse_x: Abscisse de la souris
        :type mouse_x: int
        :param mouse_y: Ordonnée de la souris
        :type mouse_y: int
        :param scale: Échelle du rendu (en m/px)
        :type scale: int
        :return: True si la souris touche l'astre sinon False
        :rtype: bool
        """
        sx, sy = self.getPosition(self.x, self.y)
        return (mouse_x - sx)**2 + (mouse_y - sy)**2 < (self.radius / scale)**2


class Earth(GraphicalCelestialBody):

    def __init__(self, x: int, y: int, image: Surface | SpriteSheet, surface: Surface, getPosition: Callable[[int, int], tuple[int, int]], goal: CelestialBody, explosion: SpriteSheet):
        """
        Réprésente la Terre et hérite de la classe GraphicalCelestialBody. La spécificité de la Terre 
        est qu'elle sert de balle de golf et donc qu'elle doit posséder des méthodes personnalisées.

        :param x: Abscisse de la Terre (en m)
        :type x: int
        :param y: Ordonnée de la Terre (en m)
        :type y: int
        :param image: Image de la Terre pour le rendu (peut être animée)
        :type image: pygame.Surface | utils.SpriteSheet
        :param surface: Surface sur laquelle afficher la Terre
        :type surface: pygame.Surface
        :param getPosition: Fonction permettant de convertir les coordonnées absolues (en m) en coordonnées relatives à l'écran (en px)
        :type getPosition: Callable[[int, int], tuple[int, int]]
        :param goal: L'astre (un trou noir / trou de ver) à atteindre pour valider le niveau
        :type goal: CelestialBody | GraphicalCelestialBody
        :param explosion: L'animation d'explosion à utiliser
        :type explosion: utils.SpriteSheet
        """
        super().__init__(x, y, 972e24, 6.4e6, image, surface, getPosition)
        self.in_black_hole = None  # Indique le trou noir dans lequel la Terre est actuellement, None si elle n'est dans aucun trou noir
        self.narrowing = 0  # Pourcentage du rétrécissement de la Terre quand elle tombe dans un trou noir
        self.fallen = False  # Est tombée dans un trou noir
        self.success = False  # A atteint la sortie
        self.original_x = x
        self.original_y = y
        self.goal = goal
        self.explosion = explosion
        self.exploding = False
        self.last_explosion_frame = 0
        self.explosion_end = False
    
    def calculateForce(self, body: CelestialBody) -> Vector:
        vector = self.getVector(body)
        # On profite du calcul des distances pour savoir si la Terre est aspirée par un trou noir
        if not self.in_black_hole and body.is_black_hole and vector.magnitude < body.radius:
            self.in_black_hole = body
        if self.in_black_hole == body:
            # Formule ajustée du calcul des forces gravitationnelles pour obtenir un mouvement naturel malgré la force du trou noir
            value = 6.6743e-11 * self.mass * body.mass / vector.magnitude / body.radius**2.9 * vector.magnitude
            return Vector(magnitude=value, direction=vector.direction)
        return super().calculateForce(body)

    def move(self, dt: float, time_scale: int) -> None:
        # Si la Terre est dans un trou noir, on diminue sa vitesse pour éviter que la force du trou noir lui donne un effet de téléportation/clignotetement
        if self.in_black_hole:
            self.speed.magnitude *= 0.999**(dt * time_scale)
            if not self.fallen:
                self.narrowing += 3 * dt
                if self.narrowing >= 3:  # Quand l'aspiration atteint 300% on considère que la Terre a disparu
                    self.fallen = True
                    self.success = self.in_black_hole is self.goal
        super().move(dt, time_scale)
        return False

    def display(self, scale: int) -> None:
        # On ajuste scale pour réduire la taille de la Terre si elle se fait aspirer par un trou noir
        if self.exploding:
            if self.explosion_end:
                return
            sx, sy = self.getPosition(self.x, self.y)
            image = self.explosion.getCurrentSprite()
            if self.explosion.frame < self.last_explosion_frame:
                self.explosion_end = True
                return
            self.last_explosion_frame = self.explosion.frame
            image = transform.scale_by(image, self.radius * 6 / scale / image.width)
            self.surface.blit(image, (sx - image.width//2, sy - image.height//2))
        else:
            if self.narrowing:
                scale += round(scale * self.narrowing)
            return super().display(scale)
    
    def reset(self) -> None:
        """
        Réinitialise la position, la vitesse et l'aspiration de la Terre pour recommencer le niveau.
        """
        self.x = self.original_x
        self.y = self.original_y
        self.narrowing = 0
        self.in_black_hole = None
        self.fallen = False
        self.locked = True
        self.explosion.frame = 0
        self.exploding = False
        self.explosion_end = False
        self.last_explosion_frame = 0
        self.stop()
    
    def collide(self) -> bool:
        """
        Vérifie les collisions avec les autres astres.

        :return: True si la Terre a percuté un astre solide, sinon False
        :rtype: bool
        """
        for body in self.other_bodies:
            if body.is_black_hole:
                continue
            if (self.x - body.x)**2 + (self.y - body.y)**2 < (self.radius + body.radius)**2:
                self.exploding = True
                return True
        return False

"""
Implémentation du modèle SPH (Smoothed Particle Hydrodynamics) pour simuler des fluides dans le jeu WaterMaze
"""

import pygame
import math
from random import randint


class SPHParticle:
    """Représente une particule seul dans la simulation"""

    def __init__(self, x=0, y=0, mass=1.0, radius=6.0)-> None:
        self.position :pygame.Vector2 = pygame.Vector2(x, y)
        self.velocity :pygame.Vector2 = pygame.Vector2(0, 0)
        self.acceleration :pygame.Vector2 = pygame.Vector2(0, 0)
        self.mass = mass
        self.radius = radius
        self.density = 1.0
        self.pressure = 0.0
        self.color = [40, 0, 255]  # bleu foncé

    def reset_acceleration(self)-> None:
        """Remet l'acceleration à 0"""
        self.acceleration = pygame.Vector2(0, 0)

    def apply_force(self, force)-> None:
        """Applique une force à une particule"""
        self.acceleration += force / self.density
        # 2nd loi de Newton: F = ma
        # Ici la densité est la masse par "paquet d'eau" et on cherche l'acceleration pour un seul

    def update(self, dt, gravity)-> None:
        """Met à jour la position de la particule en fonction de delta temps et de la gravité"""
        self.acceleration += gravity
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt
        self.acceleration = pygame.Vector2(0, 0) #Remet à 0 l'acceleration pour le prochain tick

    def draw(self, surface, camera_x, camera_y)-> None:
        """Dessine une particule sur une surface avec l'offset de la caméra"""
        draw_x = int(self.position.x - camera_x) #Position sur l'écran en x
        draw_y = int(self.position.y - camera_y) #en y


        """Le rendu est fait sur tout l'écran visible avec un offset de 50 pour éviter tout effet de 'pop' lors du déplacement"""
        if -50 < draw_x < surface.get_width() + 50 and -50 < draw_y < surface.get_height() + 50:
            pygame.draw.circle(surface, self.color, (draw_x, draw_y), int(self.radius)+15)
            
    def update_spatial_disc(self, spatial_lookup):
        spatial_lookup


class SPHSimulation:
    """Modèle d'implementation du système SPH"""

    def __init__(self, width=2500, height=900, particle_count=100)-> None:
        self.width = width
        self.height = height
        self.particles = []
        self.gravity = pygame.Vector2(0, 35)  # pixels/s²

        # Param de la sim
        self.smoothing_radius = 20.0 # Le rayon de dégradé
        self.rest_density = 9 # La densité de repo
        self.gas_stiffness = 30 # La densité du gaz ambient
        self.viscosity = 0.2 # La viscosité du liquide
        self.damping = 0.980
        
        self.cursor_radius = 150
        
        #separation de l'espace
        
        self.Y_S = int(height/self.smoothing_radius)
        self.X_S = int(width/self.smoothing_radius)
        
        self.spatial_lookup={}
        


        #spatial operations
        self.operation = [
            (0,0),
            (1,0),
            (0,1),
            (1,-1),
            (-1,1),
            (-1,-1),
            (1,1),
            (-1,0),
            (0,-1)
            
        ]
        
        # Initialise les particules
        self._initialize_particles(particle_count)
        
        

    
    def _initialize_particles(self, count:int)-> None:
        """Créer une population de particule dans une petite région

        Args:
            count (int): nombre de particules
        """
        

        particles_per_row = int(math.sqrt(count))
        spacing = 15
        start_x = self.width // 2 - (particles_per_row * spacing) // 2
        start_y = self.height // 4 

        for i in range(particles_per_row):
            for j in range(particles_per_row):
                x = start_x + i * spacing
                y = start_y + j * spacing
                new_particle=SPHParticle(x, y)
                self.particles.append(new_particle)
                
                #ajouter au spatial lookup
                cell = (int(x/self.smoothing_radius),int(y/self.smoothing_radius))
                if not cell in self.spatial_lookup:
                    self.spatial_lookup[cell]=[]
                
                self.spatial_lookup[cell].append(new_particle)
                

    def _kernel(self, distance, h)->float:
        """Cette fonction retourne l'influence (W) d'une particule à une distance donnée dans un rayon d'influence h

        Args:
            distance (int): distance
            h (int): rayon d'influence

        Returns:
            int: la valeur 
        """
        
        if distance >= h: # Si la particule est hors du rayon
            return 0.0
        
        volume = (math.pi * h**4) / 6
        return (h - distance) * (h - distance) / volume
        
        
    def _kernel_gradient(self, dst, h)->float:
        """Fonction qui retourne la valeur de gradient pour une distance donnée avec un rayon d'influence h

        Args:
            dst (float): La distance entre les particules
            h (int): Le rayon d'influence 

        Returns:
            float: La valeur de gradient
        """

        if dst >= h:return 0.0
        
        scale = (12/h**4)/6 # Dérivée de la fonction kernel
        
        return (h - dst) * scale

    def _calculate_densities(self)-> None:
        """Met à jour les densités de chaque particule de la simulation
        """
        h = self.smoothing_radius

        
        
        for particle in self.particles:
            particle.density = 0.0
            idx=int(particle.position.x/h),int(particle.position.y/h)

            for opp in self.operation:
                for other in self.spatial_lookup.get((idx[0]+opp[0],idx[1]+opp[1]), []):
                    diff = particle.position - other.position
                    distance = diff.length()
                    
                    particle.density += other.mass * self._kernel(distance, h)
                    
            particle.density = max(particle.density, 0)
                    
        

            



    def _calculate_pressures(self):
        """Calcule la pression de chaque particule à  partir de sa densité"""
        for particle in self.particles:
            particle.pressure = self.gas_stiffness*(particle.density-self.rest_density)

    def _calculate_apply_forces(self,dt):
        """Calcule les forces appliquées à chaque particules et les appliquent"""
        h = self.smoothing_radius

        

        for particle in self.particles:
            particle.reset_acceleration() # Acceleration à 0
            pressure_force = pygame.Vector2(0, 0)
            viscosity_force = pygame.Vector2(0, 0)

            idx=int(particle.position.x/h),int(particle.position.y/h)
            for opp in self.operation:
                for other in self.spatial_lookup.get((idx[0]+opp[0],idx[1]+opp[1]), []):
                    if particle is other:
                        continue

                    diff = particle.position - other.position
                    distance = diff.length()

                    
                    #- Force de pression -#
                    r = distance

                    if r > 0:
                        direction = diff / r
                    else:
                        direction = pygame.Vector2(0,0)

                    pressure_component = (
                        -(other.mass * (particle.pressure + other.pressure) /
                        (2.0 * other.density)) *
                        self._kernel_gradient(r, h)
                    )

                    pressure_force += pressure_component * direction


                    #- Force de viscosité -#
                    velocity_diff = other.velocity - particle.velocity
                    viscosity_component = (
                        self.viscosity * other.mass / other.density *
                        self._kernel(distance, h)
                    )
                    viscosity_force += velocity_diff * viscosity_component
                        


            particle.apply_force(pressure_force)
            particle.apply_force(viscosity_force)
            
            particle.update(dt, self.gravity)
            particle.velocity *= self.damping
            

        
        #Remet à 0 le dictionnaire d'optimisation spatiale
        self.spatial_lookup.clear()
            
    
    def _update_spatial_lookup(self):
        for particle in self.particles:
            cell = ((int(particle.position.x/self.smoothing_radius),int(particle.position.y/self.smoothing_radius)))
            
            if not cell in self.spatial_lookup:
                self.spatial_lookup[cell]=[]
            self.spatial_lookup[cell].append(particle)


    def _boundary_handling(self,mouse):
        """Prend en charge les collision des particules entre les bords de la simulation"""
        damping = -1
        border = 20.0 #Offset de la bordure

        for particle in self.particles:
            # Gauche
            if particle.position.x < border:
                particle.position.x = border
                particle.velocity.x *= -damping

            # Droite
            if particle.position.x > self.width - border:
                particle.position.x = self.width - border
                particle.velocity.x *= -damping

            # Haut
            if particle.position.y < border:
                particle.position.y = border
                particle.velocity.y *= -damping

            # Bas
            if particle.position.y > self.height - border:
                particle.position.y = self.height - border
                particle.velocity.y *= -damping

                

   
    def step(self, dt,mouse:tuple, stiffness, viscosity)-> None:
        """Execute un step de la simulation"""
        
        
        #Met à jour les param de la simulation selon les inputs
        self.gas_stiffness = stiffness
        self.viscosity = viscosity
        
        self.spatial_lookup.clear()
        self._update_spatial_lookup()
        
        if not self.particles:
            return

        # Calcule les densité et pression
        self._calculate_densities()
        self._calculate_pressures()


        #Verifier si le curseur est dans la simulation:
        if 0 < mouse[0] < self.width and 0 < mouse[1] < self.height:
            cell = ((int(mouse[0]/self.smoothing_radius),int(mouse[1]/self.smoothing_radius)))
            mouse_pos = pygame.Vector2(mouse[0],mouse[1])
            for opp in self.operation:
                for other in self.spatial_lookup.get((cell[0]+opp[0],cell[1]+opp[1]), []):
                    diff = other.position - mouse_pos
                    dst = diff.length()
                    
                    #Verifier la distance au curseur et appliquer la répulsion
                    if dst <= self.cursor_radius:
                        if dst <= self.cursor_radius**2:
                            
                            if dst > 0:
                                direction = diff / dst
                                strength = 100  # tweak this
                                other.velocity += direction * strength
                

        self._calculate_apply_forces(dt) #Calcule et applique les forces



        # Handle boundaries
        self._boundary_handling(mouse)


    def add_particle(self, x, y):
        """Ajoute une nouvelle particule"""
        self.particles.append(SPHParticle(x, y))

    def draw(self, surface, camera_x, camera_y):
        """Dessine toutes les particules"""
        
        """#Dessine le fond de la simulation:
        rect = pygame.Rect(0-camera_x, 0-camera_y, self.width, self.height)
        pygame.draw.rect(surface, (255,255,255), rect)"""
        
        
        for particle in self.particles:
            particle.draw(surface, camera_x, camera_y)

    def get_particle_count(self):
        """Retourne le nombre de particules"""
        return len(self.particles)

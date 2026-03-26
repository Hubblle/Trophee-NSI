# Physics.play

Physics.play est un jeu vidéo qui vous propose de jouer à des mini-jeux ou sandbox pour vous faire découvrir le monde de la physique du quotidien,le tout en utilisant des algorithmes avancés pour vous proposer un résultat balancé entre réalisme et visuel. Le but est alors simple: divertir tout en s'appuyant sur la physique naturelle.

L'idée est partie d'un constat, l'équipe était composé de deux passionnés de physique, et deux deux passionnés d'informatique,  le choix a alors été simple !

---

## ⚒️ Pré-requis

### Configuration logicielle minimale
- **OS:** Windows ≥ 10 || Linux (testé sur une version du kernel ≥ 6)
- **Python:** `≥ 3.12`
- **Modules:** Voir `requirements.txt` (ou [Installation](#installation))

### Configuration hardware minimale
Pour la majorité des mini-jeux, une configuration minimum n'est pas recommandée car ils devraient tourner sur un peu près toutes les plateformes modernes.

Il est à noter que pour faire tourner la simulation "WaterBox" la recommendation suivante est a prendre en compte pour une experience optimale;

| #          	| Minimum                          	| Recommendation                         	|
|------------	|----------------------------------	|----------------------------------------	|
| Processeur 	| `Intel i3-3100` / `AMD Ryzen 3 1200` 	| `Intel Core i5-10400` / `AMD Ryzen 5 3600` 	|

Ces recommendations sont basées sur l'idée de pouvoir faire tourner la simulation à 500-600 particules dans des conditions de stabilité totale, elles sont dû principalement à la nature single-core, et surtout dans notre cas au fait que les shaders OpenGL en GLSL sont hors programme. Les choix des processeurs sont dû à leurs haute fréquence et à leurs cache qui permet de faire tourner la boucle à un nombre de TPS plus élevé.

### Installation
Pour le bon fonctionnement du programme, plusieurs librairies sont nécessaires, pour les installer, deux scripts sont fournis;

🐧**Debian (ou debian-based distros)**
-> Bash/ZSH: `chmod +x install.sh && ./install.sh`\

-> Fish: `chmod +x install.fish && ./install.fish`\
L'un des developpeurs utilise un shell fish, c'était pour lui faire plaisir :)

**Windows (10+)**\
-> Invite de commande `./install.bat`


## ▶️ Démarrage 
Pour lancer le programme, il vous suffit d'executer le fichier `./sources/main.py` avec les [prérequis](#️-pré-requis) installés.

**Si vous avez utilisez le script d’installation**
- **Linux:**
  - Bash/ZSH: `source ./.venv/bin/activate && python3 ./sources/main.py`
  - Fish: `source ./.venv/bin/activate.fish && python3 ./sources/main.py`


- **Windows** `.venv\Scripts\python.exe sources\main.py`



## Auteurs
Le projet a été réalisé par un groupe de quatres élèves de première, tous passionnés d'informatique.

**Maxime Noé -** Développement du système de gestion des mini-jeux ainsi que des minijeux/sandbox "SpaceGolf" et le "Jeu de la vie" (ou *Conway's Game of life*)

**Lubin Tschirhart -** Rédaction des documents et documentations du dossier technique, ainsi que le développement la sandbox "WaterBox"

**Line Vacher--Drevet -** Aide à l'organisation du dossier, réalisations graphiques, aide au design et concept des jeux, ainsi qu'une aide sur le development de la sandbox "WaterBox". Responsable de la répartition des rôles et du travail ainsi que du design sonore.

**Erwan Goasdoue -** Supervision graphique du projet, aide au design, responsable des tests, et assistance au développement du jeu "SpaceGolf".

## Note: Utilisation de l'IA
Nous pensons que les intelligences artificielles peuvent être bénéfique lorsqu'elles sont utilisées de manière cohérentes et réfléchies, nous avons alors modéré nos usages, et les avons restreint à des utilisations qui ne touchent pas à une implémentation directe dans le code fournis dans le projet fini.

Tout le code et les documentation sont écrits par nos soins, seul les algorithme sont inspirés de travaux de recherches réalisés par des auteurs externes, voir la section ci dessous.

**<u>WaterBox: algorithme SPH</u>**\
Plusieurs modèles d'IA (dont Claude et GPT 5) ont été utilisés pour les recherches uniquement théoriques sur l'algorithme, ainsi que pour une fonction explicative de certains articles cités ci-dessous.

Le code en lui même n'a pas été généré par IA, il est néanmoins à noter pour la transparence que une implémentation de kernels avancés à été en partie générée par IA pour la compréhension du fonctionnement de cet algorithme, ce code a bien entendu été utilisé dans un but de test et n'a pas été transféré de quelconque manière dans le projet final.

**Sources externes**\
Veuillez trouver ci-dessous une liste des sources et médias consultés pour la réalisation de cette partie du projet.

- https://sph-tutorial.physics-simulation.org/pdf/SPH_Tutorial.pdf : Un article très avancé qui a été très bénéfique pour comprendre le fond de l'algorithme et ses enjeux.
- https://www.youtube.com/watch?v=rSKMYc1CQHE&t=486s : Une vidéo qui détail une implémentation de l'algorithme, c'est celle ci qui a initialement donnée l'idée d'utiliser cet algorithme, ainsi que les formules des kernel utilisés.
- https://deepwiki.com/yuki-koyama/position-based-fluids/1-position-based-fluids-overview : La documentation d'un algorithme alternatif qui a tout de même été bénéfique au projet.
- https://github.com/AyB2003/Pygame_Water_Simulator/tree/main : Un exemple d'implémentation de l'algorithme Open-source en python, qui a été utilisé pour mieux appréhender l'implémentation de l'agorithme avec Pygame.
- https://en.wikipedia.org/wiki/Smoothed-particle_hydrodynamics : Pour une explication plus vulgarisé de certaines equations.

**<u>Conway's Game of Life: algorithme du HashLife </u>**\
Pour ce projet, une source externe a été utilisée pour la compréhension ainsi que la découverte de l'algorithme: https://www.dev-mind.blog/hashlife/




## 🔏 License

Ce projet est sous licence GPL-3.0 - voir le fichier [LICENSE](LICENSE) pour plus d'informations

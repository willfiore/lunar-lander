###################################
########## Lunar Lander ###########
#### Created by: William Fiore ####
###################################

## Controls: ##
# Arrow Keys # Control lander
#          R # Restart game

import sys

from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

import copy
import math
import random
from enum import Enum, IntEnum

class GameState(Enum):
    startScreen = 0
    ingame = 1

class SpecialKey(IntEnum):
    left = 100
    up = 101
    right = 102

class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Lander:    
    startingFuel = 100
    fuelConsumptionRate = 10 # fuel consumed per second
    
    thrusterStrength = 55 # make this larger than gravity!
    sideThrusterStrength = 2

    size = Vector2(20, 25)
    
    def __init__(self):
        self.position = Vector2(random.randint(0, glutGet(GLUT_WINDOW_WIDTH)), glutGet(GLUT_WINDOW_HEIGHT)-20)
        self.velocity = Vector2(random.randint(-20, 20), 0)
        self.acceleration = Vector2(0, 0)
        
        self.rotation = random.randint(-20, 20)
        self.rotationVelocity = 0
        #self.rotationAcceleration = 0
        
        self.fuel = self.startingFuel

class FuelParticle:
    speed = 3
    defaultLifetime = 0.5
    defaultSize = 4
    
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.rotation = 0
        self.rotationVelocity = 0
        self.lifetime = 0
        self.currentLifetime = 0
        self.size = self.defaultSize

### GLOBALS ###

DEFAULT_WINDOW_WIDTH  = 720
DEFAULT_WINDOW_HEIGHT = 480
aspectRatio = DEFAULT_WINDOW_WIDTH / DEFAULT_WINDOW_HEIGHT # dynamically changed on resize

gameState = GameState.startScreen

keysDown = {}

terrainPointDensity = 25 # lower numbers create more rocky terrain
terrainMinHeight = 20
terrainStartHeight = 100
terrainMaxHeight = 400
terrainVariation = 20
terrainPoints = []

landingAreaPosition = Vector2(0,0) # top-left coordinate of the landing area
landingAreaWidth = Lander.size.x + 20

gravity = -30

numStars = 1000
stars = []

fuelParticles = []

# w2r: converts world coordinates to render coordinates
def w2r(coordinates):
    windowWidth = glutGet(GLUT_WINDOW_WIDTH)
    windowHeight = glutGet(GLUT_WINDOW_HEIGHT)
    x = aspectRatio*(2*(coordinates.x / windowWidth) - 1)
    y = 2*(coordinates.y / windowHeight) - 1
    return Vector2(x, y)

def createStars():
    del stars[:]
    for i in range(numStars):
        # Stars are stored as [x, y, opacity]
        # I don't use world coordinates for stars since they are just a static background
        stars.append([random.randint(-2000, 2000), random.randint(-2000, 2000), random.randint(0, 100)])

def createTerrain():
    # terrain is created as a series of points on the surface
    del terrainPoints[:]

    firstPoint = Vector2(0, random.randint(terrainMinHeight, (terrainMaxHeight + terrainMinHeight)/2))
    
    global landingAreaPosition
    # pick a random x position for the landing area
    landingAreaPosition = Vector2(random.randint(0, glutGet(GLUT_WINDOW_WIDTH) - landingAreaWidth), 0)    
    doneLandingArea = False

    terrainPoints.append(firstPoint)
    
    while (terrainPoints[-1].x < glutGet(GLUT_WINDOW_WIDTH)):
        prevPoint = terrainPoints[-1]
        point = copy.copy(prevPoint)

        # slightly randomize x position of next point
        point.x += random.randint(12, 15)
        # y position randomized but close to previous point (and not exceeding max and min height)
        point.y = random.randint(max(terrainMinHeight, prevPoint.y - terrainVariation), min(terrainMaxHeight, prevPoint.y + terrainVariation))

        # create landing area
        if(point.x >= landingAreaPosition.x and not doneLandingArea):
            # move the point to exactly where the landing area was chosen
            point.x = landingAreaPosition.x
            terrainPoints.append(copy.copy(point))
            # create right side of landing area horizontally to the right
            terrainPoints.append(Vector2(point.x + landingAreaWidth, point.y))

            # we now know the y position of the landing area
            landingAreaPosition.y = point.y
            doneLandingArea = True
            
        # create normal terrain point
        else:
            terrainPoints.append(copy.copy(point))

def restartGame():
    createStars()
    createTerrain()
    respawnLander()

def respawnLander():
    global lander
    del lander
    lander = Lander()

def keyboardDown(keyCode, mouseX, mouseY):
    # Add key to keys down dictionary
    keysDown[keyCode] = True

    # quick-fire presses
    if (keyCode == b'r'):
        restartGame()

def keyboardUp(keyCode, mouseX, mouseY):
    keysDown[keyCode] = False
    del keysDown[keyCode]

def keyboardSpecialDown(keyCode, mouseX, mouseY):
    keysDown[keyCode] = True

def keyboardSpecialUp(keyCode, mouseX, mouseY):
    keysDown[keyCode] = False
    del keysDown[keyCode]

lastUpdateTime = 0
updateRate = 15 # milliseconds
def tick():
    global lastUpdateTime
    # Only update the game logic in a fixed interval
    timeSinceLastUpdate = glutGet(GLUT_ELAPSED_TIME) - lastUpdateTime
    while(timeSinceLastUpdate > updateRate):
        lastUpdateTime = glutGet(GLUT_ELAPSED_TIME)
        timeSinceLastUpdate -= updateRate
        update(lastUpdateTime, updateRate)

    # Draw to the screen as fast as possible
    render()


lastFuelParticle = 0
def update(lastUpdateTime, dt):
    dt = dt / 1000 # convert dt to seconds (to work nicely with physics equations)

    ### LANDER PHYSICS ###    
    # using velocity verlet integration for more precision
    lander.position.x += dt * (lander.velocity.x + dt * lander.acceleration.x / 2)
    lander.position.y += dt * (lander.velocity.y + dt * lander.acceleration.y / 2)

    # just euler integration for velocity
    lander.velocity.x += dt * lander.acceleration.x
    lander.velocity.y += dt * lander.acceleration.y
    
    lander.rotation += lander.rotationVelocity

    # initialise default lander movement values
    lander.acceleration.x = 0
    lander.acceleration.y = gravity
    lander.rotationVelocity = 0

    ### FUEL PARTICLE PHYSICS ###
    for particle in fuelParticles[:]:
        particle.position.x += particle.velocity.x
        particle.position.y += particle.velocity.y
        particle.rotation += particle.rotationVelocity
        particle.currentLifetime += dt

        # remove old particles
        if (particle.currentLifetime > particle.lifetime):
            fuelParticles.remove(particle)

    ### LANDER CONTROLS ###
    # do not accept control if no fuel
    if (lander.fuel <= 0): return
    
    if (keysDown.get(SpecialKey.up)):
        lander.acceleration.x = Lander.thrusterStrength * math.sin(math.radians(lander.rotation))
        lander.acceleration.y = gravity + Lander.thrusterStrength * math.cos(math.radians(lander.rotation))
        lander.fuel -= Lander.fuelConsumptionRate * dt # 10 fuel per second

        # create fuel particles
        global lastFuelParticle
        if (lastUpdateTime - lastFuelParticle > 20):
            fuelParticle = FuelParticle(lander.position.x, lander.position.y)
            fuelParticle.velocity.x = -FuelParticle.speed * math.sin(math.radians(lander.rotation + random.randint(-25, 25)))
            fuelParticle.velocity.y = -FuelParticle.speed * math.cos(math.radians(lander.rotation + random.randint(-25, 25)))
            fuelParticle.rotation = random.randint(0, 90)
            fuelParticle.rotationVelocity = 1 if random.randrange(2) else -1
            fuelParticle.lifetime = random.uniform(FuelParticle.defaultLifetime, FuelParticle.defaultLifetime + 1)
            fuelParticles.append(fuelParticle)
            
            lastFuelParticle = lastUpdateTime

    if (keysDown.get(SpecialKey.left)):
        lander.rotationVelocity = -Lander.sideThrusterStrength
        lander.fuel -= Lander.fuelConsumptionRate * dt * 0.5
    elif (keysDown.get(SpecialKey.right)):
        lander.rotationVelocity = Lander.sideThrusterStrength
        lander.fuel -= Lander.fuelConsumptionRate * dt * 0.5

def drawTerrain():
    #renderCoordinates = None
    glBegin(GL_TRIANGLES)
    glColor(0.65, 0.7, 0.7)
    
    for i in range(len(terrainPoints)-1):
        renderCoordinates = w2r(terrainPoints[i])
        nextCoordinates = w2r(terrainPoints[i+1])

        # Terrain is a concave polygon, so it must be
        # split into triangles:
        
        # triangle 1
        glVertex2f(renderCoordinates.x, renderCoordinates.y) # first terrain point
        glVertex2f(nextCoordinates.x, nextCoordinates.y)     # second terrain point
        glVertex2f(renderCoordinates.x, w2r(Vector2(0,0)).y) # bottom of screen below first terrain point

        # triangle 2
        glVertex2f(renderCoordinates.x, w2r(Vector2(0,0)).y) # bottom of screen below first terrain point
        glVertex2f(nextCoordinates.x, w2r(Vector2(0,0)).y)   # bottom of screen below second terrain point
        glVertex2f(nextCoordinates.x, nextCoordinates.y)     # second terrain point
            
    glEnd()

def drawLandingArea():
    glBegin(GL_POLYGON)
    glColor(1.0, 1.0, 0.0)

    left = w2r(landingAreaPosition)

    landingAreaPositionRight = copy.copy(landingAreaPosition)
    landingAreaPositionRight.x += landingAreaWidth

    right = w2r(landingAreaPositionRight)

    glVertex2f(left.x, left.y)
    glVertex2f(right.x, right.y)

    glColor(0.0, 1.0, 0.0, 0.0)
    
    glVertex2f(right.x, -1)
    glVertex2f(left.x, -1)
    glEnd()

def drawLander():
    bottomLeft = w2r(Vector2(lander.position.x - lander.size.x/2, lander.position.y - lander.size.y/2))
    bottomRight = w2r(Vector2(lander.position.x + lander.size.x/2, lander.position.y - lander.size.y/2))
    topLeft = w2r(Vector2(lander.position.x - lander.size.x/2, lander.position.y + lander.size.y/2))
    topRight = w2r(Vector2(lander.position.x + lander.size.x/2, lander.position.y + lander.size.y/2))

    glPushMatrix()
    glTranslatef(w2r(lander.position).x, w2r(lander.position).y, 0)
    glRotate(-lander.rotation, 0, 0, 1)
    glTranslatef(-w2r(lander.position).x, -w2r(lander.position).y, 0)

    glBegin(GL_POLYGON)
    glColor(0.7, 0.7, 0.7, 1.0)
    glVertex2f(bottomLeft.x, bottomLeft.y)
    glVertex2f(bottomRight.x, bottomRight.y)
    glColor(1.0, 1.0, 1.0, 1.0)
    glVertex2f(topRight.x, topRight.y)
    glVertex2f(topLeft.x, topLeft.y)
    glEnd()
    
    glPopMatrix()

def drawStars():
    glBegin(GL_POINTS)
    for i in range(numStars):
        opacity = stars[i][2]/100
        glColor(opacity, opacity, opacity)
        glVertex2f(aspectRatio*stars[i][0]/2000, stars[i][1]/2000)
    glEnd()
        
def drawFuelParticles():
    for particle in fuelParticles:

        # randomize size every frame + get larger towards end of life
        particle.size = random.uniform(FuelParticle.defaultSize -1, FuelParticle.defaultSize + 1) + (particle.currentLifetime/particle.lifetime)*10
        
        topLeft = w2r(Vector2(particle.position.x - particle.size, particle.position.y + particle.size))
        topRight = w2r(Vector2(particle.position.x + particle.size, particle.position.y + particle.size))
        bottomLeft = w2r(Vector2(particle.position.x - particle.size, particle.position.y - particle.size))
        bottomRight = w2r(Vector2(particle.position.x + particle.size, particle.position.y - particle.size))

        glPushMatrix()
        glTranslatef(w2r(particle.position).x, w2r(particle.position).y, 0)
        glRotate(-particle.rotation, 0, 0, 1)
        glTranslatef(-w2r(particle.position).x, -w2r(particle.position).y, 0)

        glBegin(GL_POLYGON)

        redFlicker = random.uniform(0.6, 0.9)
        greenFlicker = random.uniform(0.3, 0.6)
        
        glColor4f(redFlicker, greenFlicker, 0, 0.7 * (particle.lifetime - particle.currentLifetime)/particle.lifetime)
        glVertex2f(topLeft.x, topLeft.y)
        glVertex2f(topRight.x, topRight.y)
        glVertex2f(bottomRight.x, bottomRight.y)
        glVertex2f(bottomLeft.x, bottomLeft.y)
        glEnd()

        glPopMatrix()

def render():    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    drawStars()
    drawFuelParticles()
    drawTerrain()
    drawLandingArea()
    drawLander()
    glutSwapBuffers()

# Initialise OpenGL window
glutInit(sys.argv)
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH | GLUT_MULTISAMPLE)
glutInitWindowSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
glutCreateWindow("SuperLander")

def onWindowResize(width, height):
    global aspectRatio
    aspectRatio = width / height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-1.0 * aspectRatio, 1.0 * aspectRatio, -1.0, 1.0)

# Set GLUT function hooks
glutKeyboardFunc(keyboardDown)
glutKeyboardUpFunc(keyboardUp)
glutSpecialFunc(keyboardSpecialDown)
glutSpecialUpFunc(keyboardSpecialUp)

glutDisplayFunc(render)
glutIdleFunc(tick)
glutReshapeFunc(onWindowResize)

glEnable(GL_BLEND)
glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
glClearColor(0.0, 0.0, 0.05, 1.0)

createStars()
createTerrain()

lander = Lander()

glutMainLoop()

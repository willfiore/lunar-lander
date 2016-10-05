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
    postgame = 2

class PostGameState(Enum):
    none = 0
    success = 1
    tooFast = 2
    sideways = 3
    missedLandingArea = 4

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

    maxLandingVelocity = 40
    maxLandingRotation = 10

    size = Vector2(20, 25)
    
    def __init__(self):
        self.position = Vector2(random.randint(0, glutGet(GLUT_WINDOW_WIDTH)), glutGet(GLUT_WINDOW_HEIGHT)-20)
        self.velocity = Vector2(random.randint(-20, 20), 0)
        self.acceleration = Vector2(0, 0)
        
        self.rotation = random.randint(-20, 20)
        self.rotationVelocity = 0
        #self.rotationAcceleration = 0
        
        self.fuel = self.startingFuel
        self.hitGround = False
        self.visible = True

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
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 480

aspectRatio = DEFAULT_WINDOW_WIDTH / DEFAULT_WINDOW_HEIGHT # dynamically changed on resize

gameState = GameState.ingame
postGameState = PostGameState.none

keysDown = {}

terrainPointDensity = 25 # lower numbers create more rocky terrain
terrainMinHeight = 20
terrainStartHeight = 100
terrainMaxHeight = 400
terrainVariationY = 10
terrainMinXSpacing = 12
terrainMaxXSpacing = 15
terrainPoints = []

landingAreaPosition = Vector2(0,0) # top-left coordinate of the landing area
landingAreaWidth = 0

gravity = -30

numStars = 300
stars = []

fuelParticles = []

fuelBarWidth = 20
fuelBarHeight = 200

# w2r: converts world coordinates to render coordinates
def w2r(coordinates):
    windowWidth = glutGet(GLUT_WINDOW_WIDTH)
    windowHeight = glutGet(GLUT_WINDOW_HEIGHT)
    x = aspectRatio*(2*(coordinates.x / windowWidth) - 1)
    y = 2*(coordinates.y / windowHeight) - 1
    return Vector2(x, y)

def rotateAround(point, origin, angle):
    angle = math.radians(angle) # convert angle to radians

    diff = Vector2(point.x - origin.x, point.y - origin.y)
    trans = Vector2(diff.x * math.cos(angle) - diff.y * math.sin(angle),
                    diff.x * math.sin(angle) + diff.y * math.cos(angle))

    point.x = origin.x + trans.x
    point.y = origin.y + trans.y

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
    global landingAreaWidth
    # randomize landing area width to an extent
    landingAreaWidth = Lander.size.x + random.randint(10, 40)
    # pick a random x position for the landing area
    landingAreaPosition = Vector2(random.randint(0, glutGet(GLUT_WINDOW_WIDTH) - landingAreaWidth), 0)    
    doneLandingArea = False

    terrainPoints.append(firstPoint)
    
    while (terrainPoints[-1].x < glutGet(GLUT_WINDOW_WIDTH)):
        prevPoint = terrainPoints[-1]
        point = copy.copy(prevPoint)

        # slightly randomize x position of next point
        point.x += random.randint(terrainMinXSpacing, terrainMaxXSpacing)
        # y position randomized but close to previous point (and not exceeding max and min height)
        point.y = random.randint(max(terrainMinHeight, prevPoint.y - terrainVariationY), min(terrainMaxHeight, prevPoint.y + terrainVariationY))

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

def doCollisionDetection():
    # line intersection helper functions
    # taken from http://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
    def ccw(A, B, C):
        return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
    
    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
            
    landerCorners = [Vector2(lander.position.x - lander.size.x/2, lander.position.y + lander.size.y/2),
                     Vector2(lander.position.x + lander.size.x/2, lander.position.y + lander.size.y/2),
                     Vector2(lander.position.x + lander.size.x/2, lander.position.y - lander.size.y/2),
                     Vector2(lander.position.x - lander.size.x/2, lander.position.y - lander.size.y/2)]

    # rotate corners
    for i in range(len(landerCorners)):
        rotateAround(landerCorners[i], lander.position, -lander.rotation)

    # collect the terrain points we need to analyse
    # simple bounding box: terrain bisecting lander cannot be outside this range
    minTerrainX = lander.position.x - max(lander.size.x, lander.size.y)/2 - max(terrainMaxXSpacing, landingAreaWidth)
    maxTerrainX = lander.position.x + max(lander.size.x, lander.size.y)/2 + max(terrainMaxXSpacing, landingAreaWidth)

    terrainToCheck = []
    for point in terrainPoints:
        # start from the left:
        # if we havent reached minTerrainX, continue to next point
        if point.x < minTerrainX: continue
        # if we have gone too far, break out of the loop
        if point.x > maxTerrainX: break
        terrainToCheck.append(point) # found a good point!

    for i in range(len(terrainToCheck) - 1):
        terrain1 = terrainToCheck[i]
        terrain2 = terrainToCheck[i+1]

        for j in range(len(landerCorners)):
            lander1 = landerCorners[j]
            lander2 = landerCorners[j+1] if j < 3 else landerCorners[0]

            if (intersect(terrain1, terrain2, lander1, lander2)):
                lander.hitGround = True

                global postGameState
                if (abs(lander.velocity.y) > Lander.maxLandingVelocity):
                    explodeLander()
                    postGameState = PostGameState.tooFast
                elif (terrain1.x != landingAreaPosition.x):
                    explodeLander()
                    postGameState = PostGameState.missedLandingArea
                elif (abs(lander.rotation) > Lander.maxLandingRotation):
                    explodeLander()
                    postGameState = PostGameState.sideways
                else:
                    onSuccessfulLanding()
                    postGameState = PostGameState.success

                return

def onSuccessfulLanding():
    lander.rotation = 0

def explodeLander():
    lander.visible = False

    numExplosionParticles = 20
    for i in range(numExplosionParticles):
        fuelParticle = FuelParticle(lander.position.x, lander.position.y)
        fuelParticle.velocity.x = -FuelParticle.speed * math.sin(math.radians((i/numExplosionParticles)*360 + random.randint(-25, 25)))
        fuelParticle.velocity.y = -FuelParticle.speed * math.cos(math.radians((i/numExplosionParticles)*360 + random.randint(-25, 25)))
        fuelParticle.rotation = random.randint(0, 90)
        fuelParticle.rotationVelocity = 1 if random.randrange(2) else -1
        fuelParticle.lifetime = FuelParticle.defaultLifetime*2
        fuelParticles.append(fuelParticle)
    
            
def restartGame():
    global postGameState
    postGameState = PostGameState.none
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

    if (not lander.hitGround):
        ### LANDER PHYSICS ###    
        # using velocity verlet integration for more precision at a fixed timestep
        lander.position.x += dt * (lander.velocity.x + dt * lander.acceleration.x / 2)
        lander.position.y += dt * (lander.velocity.y + dt * lander.acceleration.y / 2)
        
        # just euler integration for velocity
        lander.velocity.x += dt * lander.acceleration.x
        lander.velocity.y += dt * lander.acceleration.y
        
        lander.rotation += lander.rotationVelocity

        # wrap rotation values
        while (lander.rotation >= 180):
            lander.rotation -= 360

        while (lander.rotation < -180):
            lander.rotation += 360
            
        # initialise default lander movement values
        lander.acceleration.x = 0
        lander.acceleration.y = gravity
        lander.rotationVelocity = 0

        doCollisionDetection()

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
    # do not accept control if no fuel or touched ground
    if (lander.fuel <= 0):
        lander.fuel = 0
        return
    if (lander.hitGround):
        return

    # upwards thruster key
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

    # rotation keys
    if (keysDown.get(SpecialKey.left)):
        lander.rotationVelocity = -Lander.sideThrusterStrength
        lander.fuel -= Lander.fuelConsumptionRate * dt * 0.5
    elif (keysDown.get(SpecialKey.right)):
        lander.rotationVelocity = Lander.sideThrusterStrength
        lander.fuel -= Lander.fuelConsumptionRate * dt * 0.5

## DRAWING FUNCTIONS ##
        
def drawTerrain():
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
    glBegin(GL_POLYGON) # simple rectangle
    glColor(1.0, 1.0, 0.0)

    left = w2r(landingAreaPosition)

    landingAreaPositionRight = copy.copy(landingAreaPosition)
    landingAreaPositionRight.x += landingAreaWidth

    right = w2r(landingAreaPositionRight)

    # draw first two points on surface
    glVertex2f(left.x, left.y)
    glVertex2f(right.x, right.y)

    # fade out gradient
    glColor(0.0, 1.0, 0.0, 0.0)

    # to bottom of screen
    glVertex2f(right.x, -1)
    glVertex2f(left.x, -1)
    
    glEnd()

def drawLander():
    if not lander.visible: return
    # establish corners before rotation
    landerCorners = [Vector2(lander.position.x - lander.size.x/2, lander.position.y + lander.size.y/2),
                     Vector2(lander.position.x + lander.size.x/2, lander.position.y + lander.size.y/2),
                     Vector2(lander.position.x + lander.size.x/2, lander.position.y - lander.size.y/2),
                     Vector2(lander.position.x - lander.size.x/2, lander.position.y - lander.size.y/2)]

    # rotate and convert corners to screen coordinates
    for i in range(len(landerCorners)):
        rotateAround(landerCorners[i], lander.position, -lander.rotation)
        landerCorners[i] = w2r(landerCorners[i])

    glBegin(GL_POLYGON)
    glColor(1.0, 1.0, 1.0, 1.0)
    glVertex2f(landerCorners[0].x, landerCorners[0].y)
    glVertex2f(landerCorners[1].x, landerCorners[1].y)
    glColor(0.7, 0.7, 0.7, 1.0)
    glVertex2f(landerCorners[2].x, landerCorners[2].y)
    glVertex2f(landerCorners[3].x, landerCorners[3].y)
    glEnd()
    
    # glPopMatrix()

def drawStars():
    glBegin(GL_POINTS)
    for i in range(numStars):
        opacity = stars[i][2]/100
        glColor(opacity, opacity, opacity)
        glVertex2f(aspectRatio*stars[i][0]/2000, stars[i][1]/2000)
    glEnd()

# very similar to lander.. maybe i could create a drawRectangle function
def drawFuelParticles():
    for particle in fuelParticles:

        # randomize size every frame + get larger towards end of life
        particle.size = random.uniform(FuelParticle.defaultSize -1, FuelParticle.defaultSize + 1) + (particle.currentLifetime/particle.lifetime)*10
        
        fuelParticleCorners = [Vector2(particle.position.x - particle.size, particle.position.y + particle.size),
                               Vector2(particle.position.x + particle.size, particle.position.y + particle.size),
                               Vector2(particle.position.x + particle.size, particle.position.y - particle.size),
                               Vector2(particle.position.x - particle.size, particle.position.y - particle.size)]

        for i in range(len(fuelParticleCorners)):
            rotateAround(fuelParticleCorners[i], particle.position, particle.rotation)
            fuelParticleCorners[i] = w2r(fuelParticleCorners[i])

        # flicker colour every frame - cool effect
        redFlicker = random.uniform(0.6, 0.9)
        greenFlicker = random.uniform(0.3, 0.6)
            
        glBegin(GL_POLYGON)        
        glColor4f(redFlicker, greenFlicker, 0, 0.7 * (particle.lifetime - particle.currentLifetime)/particle.lifetime)

        for i in range(len(fuelParticleCorners)):
            glVertex2f(fuelParticleCorners[i].x, fuelParticleCorners[i].y)
        glEnd()


def drawFuelBar():
    fuelPercentage = lander.fuel / lander.startingFuel
    # draw bg
    glBegin(GL_POLYGON)
    glColor(0.5, 0.5, 0.5)
    topLeft = w2r(Vector2(20, WINDOW_HEIGHT - 20))
    topRight = w2r(Vector2(20 + fuelBarWidth, WINDOW_HEIGHT - 20))
    bottomLeft = w2r(Vector2(20, WINDOW_HEIGHT - (20 + fuelBarHeight)))
    bottomRight = w2r(Vector2(20 + fuelBarWidth, WINDOW_HEIGHT - (20 + fuelBarHeight)))

    glVertex2f(topLeft.x, topLeft.y)
    glVertex2f(topRight.x, topRight.y)
    glVertex2f(bottomRight.x, bottomRight.y)
    glVertex2f(bottomLeft.x, bottomLeft.y)
    glEnd()
    
    # draw bar
    glBegin(GL_POLYGON)
    glColor(1.0, 0.0, 0.0)

    barHeight = fuelBarHeight * fuelPercentage
    barTopLeft = w2r(Vector2(20, WINDOW_HEIGHT - 20 - fuelBarHeight + barHeight))
    barTopRight = w2r(Vector2(20 + fuelBarWidth, WINDOW_HEIGHT - 20 - fuelBarHeight + barHeight))
    
    glVertex2f(bottomRight.x, bottomRight.y)
    glVertex2f(bottomLeft.x, bottomLeft.y)

    # fade top of fuel bar from yellow to red
    glColor(1.0, fuelPercentage, 0.0)
    
    glVertex2f(barTopLeft.x, barTopLeft.y)
    glVertex2f(barTopRight.x, barTopRight.y)
    glEnd()

    # write fuel number next to bar
    fuelString = str(math.floor(lander.fuel))
    drawText(Vector2(20 + 10 + fuelBarWidth, WINDOW_HEIGHT - 20 - 10 - fuelBarHeight + barHeight),
             GLUT_BITMAP_9_BY_15, fuelString, 1.0, fuelPercentage, 0.0)

def drawControls():
    drawText(Vector2(WINDOW_WIDTH - 180, WINDOW_HEIGHT - 22), GLUT_BITMAP_9_BY_15, "Arrow keys to move", 1.0, 1.0, 1.0)
    drawText(Vector2(WINDOW_WIDTH - 125, WINDOW_HEIGHT - 40), GLUT_BITMAP_9_BY_15, "R to restart", 1.0, 1.0, 1.0)

def drawSuccessText():
    drawText(Vector2(WINDOW_WIDTH / 2 - (21*9+21)/2, WINDOW_HEIGHT / 2 + 70), GLUT_BITMAP_9_BY_15, "LANDED SUCCESSFULLY!!", 0.0, 1.0, 0.0)
    drawText(Vector2(WINDOW_WIDTH / 2 - (21*9+21)/2, WINDOW_HEIGHT / 2 + 50), GLUT_BITMAP_9_BY_15, "Press R to play again", 1.0, 1.0, 1.0)

def drawFailCrashFastText():
    drawText(Vector2(WINDOW_WIDTH / 2 - (33*9+33)/2, WINDOW_HEIGHT / 2 + 70), GLUT_BITMAP_9_BY_15, "CRASHED! Hit the ground too fast!", 1.0, 0.0, 0.0)
    drawText(Vector2(WINDOW_WIDTH / 2 - (20*9+20)/2, WINDOW_HEIGHT / 2 + 50), GLUT_BITMAP_9_BY_15, "Press R to try again", 1.0, 1.0, 1.0)

def drawFailCrashSidewaysText():
    drawText(Vector2(WINDOW_WIDTH / 2 - (29*9+29)/2, WINDOW_HEIGHT / 2 + 70), GLUT_BITMAP_9_BY_15, "CRASHED! Didn't land upright!", 1.0, 0.0, 0.0)
    drawText(Vector2(WINDOW_WIDTH / 2 - (20*9+20)/2, WINDOW_HEIGHT / 2 + 50), GLUT_BITMAP_9_BY_15, "Press R to try again", 1.0, 1.0, 1.0)

def drawFailMissedLandingAreaText():
    drawText(Vector2(WINDOW_WIDTH / 2 - (32*9+32)/2, WINDOW_HEIGHT / 2 + 70), GLUT_BITMAP_9_BY_15, "FAILED! Missed the landing area!", 1.0, 0.0, 0.0)
    drawText(Vector2(WINDOW_WIDTH / 2 - (20*9+20)/2, WINDOW_HEIGHT / 2 + 50), GLUT_BITMAP_9_BY_15, "Press R to try again", 1.0, 1.0, 1.0)

def drawText(position, font, text, r, g, b):
    position = w2r(position)

    glColor(r, g, b, 1.0)
    glRasterPos2f(position.x, position.y)
    for ch in text:
        glutBitmapCharacter(font, ctypes.c_int(ord(ch)))
    

def render():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    drawStars()
    drawFuelParticles()
    drawTerrain()
    drawLandingArea()
    drawLander()
    drawFuelBar()
    drawControls()

    if postGameState == PostGameState.success:
        drawSuccessText()
    elif postGameState == PostGameState.tooFast:
        drawFailCrashFastText()
    elif postGameState == PostGameState.sideways:
        drawFailCrashSidewaysText()
    elif postGameState == PostGameState.missedLandingArea:
        drawFailMissedLandingAreaText()
        
    glutSwapBuffers()

# Initialise OpenGL window
glutInit(sys.argv)
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH | GLUT_MULTISAMPLE)
glutInitWindowSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
glutCreateWindow("lander")

def onWindowResize(width, height):
    global aspectRatio
    aspectRatio = width / height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-1.0 * aspectRatio, 1.0 * aspectRatio, -1.0, 1.0)
    
    global WINDOW_WIDTH
    global WINDOW_HEIGHT

    WINDOW_WIDTH = width
    WINDOW_HEIGHT = height

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

# initialize first game
lander = None
restartGame()

glutMainLoop()

import json
import os
import random
import bottle

from api import ping_response, start_response, move_response, end_response

directions = ["up", "down", "left", "right"]

def safe_squares(square, dangerSquares):
    """
        returs the safe squares adjacent to square
    """
    safeSquares = []
    for move in directions:
        adjSquare = one_move(square, move)
        if adjSquare not in dangerSquares:
            safeSquares.append(adjSquare)
    return safeSquares
    
def BFS_dist(source, sink, maxLen, data):
    """
       returns bfs search distance, no more than maxLen squares
       returns infinity if all paths exhausted before finding


       TODO: return error instead of infinity?
    """
##    directions = ["up", "down", "left", "right"]
    if source == sink:
        return 0
    
    dangerSquares = danger_squares(data)
    height = data['board']["height"]
    width = data['board']["width"]
    
    safeSquares = safe_squares(source, dangerSquares)
             
    paths = []
    discoveredSquares = []
    
    ## check if adjacent to sink
    for move in directions:
        firstStep = one_move(source, move)
        if firstStep == sink:
            return 1
    
    ## start paths with safe squares
    for square in safeSquares:
        discoveredSquares.append(square)
        startPath = [square]
        paths.append(startPath)
        
    
    for i in range(2, maxLen + 1):
        longerPaths = []
        for path in paths:
            frontier = path[-1]    ## for each path, the frontier is the last visited square in the path
            
            for move in directions:
                nextSquare = one_move(frontier, move)
                if nextSquare is sink:
                    return i
                
            safeSquares = safe_squares(frontier, dangerSquares)
            for square in safeSquares:
                ##nextSquare = one_move(frontier, move)
                if square not in discoveredSquares:
                    newPath = list(path) ## a copy of the path
                    newPath.append(square)
                    discoveredSquares.append(square)
                    longerPaths.append(newPath)
        paths = longerPaths               ## next time through the loop, we will build off new longer paths
        if len(paths) == 0:
            return float("inf")    ##if no paths from source to sink, distance = infinity
    return i    ## returns maxLen if no path found before maxLen

def danger_squares(data):
    '''
    Takes in game data and returns dangerous squares (out of bounds, snake bodies)
    '''
    dangerSquares = []
    for snek in data['board']['snakes']:    #other sneks not safe
        for square in snek['body']:
            dangerSquares.append(square)
    for square in data['you']['body']:    ##head and body not safe 
        dangerSquares.append(square)
        
    height = data['board']["height"]
    width = data['board']["width"]
    
    for i in range(width):
        dangerSquares.append({"x":i, "y":-1})
        dangerSquares.append({"x":i, "y":height})
        
    for i in range(height):
        dangerSquares.append({"x":-1, "y":i})
        dangerSquares.append({"x":width, "y":i})
    
    return dangerSquares
    
def snek_dist(sq1,sq2):
    '''
    takes in two x,y tuples and returns taxicab distance
    '''
    dx = abs(sq1["x"]-sq2["x"])
    dy = abs(sq1["y"]-sq2["y"])
    return dx + dy

def one_move(square, direction):
    '''
    takes in a square and a direction and returns the square one step in that direction
    '''
    newSquare = {"x": 0, "y":0}
    if direction == "up":
        newSquare["x"] = square["x"]
        newSquare["y"] = square["y"] - 1
    elif direction == "down":
        newSquare["x"] = square["x"]
        newSquare["y"] = square["y"] + 1
    elif direction == "left":
        newSquare["x"] = square["x"] - 1
        newSquare["y"] = square["y"]
    elif direction == "right":
        newSquare["x"] = square["x"] + 1
        newSquare["y"] = square["y"]
    return newSquare

def square_score(square, data):
    '''
    This functon scores a square based on how close it is to food, bigger snakes,
    and smaller snakes. A higher score should correspond to a better move.
    '''
    myLength = len(data['you']['body'])
    foods = data['board']['food']
    
    scarySneks = []
    yummySneks = []
    for snek in data['board']['snakes']:
        if len(snek['body'])>= myLength:
            scarySneks.append(snek['body'])
        else:
            yummySneks.append(snek['body'])
    
    score = 0
    maxBFSDist = 8
    ## decrease near scary snek head, increase toward scary snake tail
    for snek in scarySneks:
        snekDist = BFS_dist(square, snek[0], maxBFSDist, data)
        if snekDist == 1:
            score = score - 4              # adjacent to head is bad
        elif snekDist == 2 or snekDist == 3:
            score = score - 4/snekDist # or kind of close to head is bad
            
        tailDist = BFS_dist(square, snek[-1], maxBFSDist, data)
        if tailDist == 1:                  #follow a closish tail
            score = score + 3
        elif tailDist == 2:
            score = score + 1   
            
            
    for snek in yummySneks:
        snekDist = BFS_dist(square, snek[0], maxBFSDist, data)
        if snekDist == 1:
            score = score + 3 # eat yummy sneks
        else:
            score = score + 2/snekDist
            
    # when to eat? 
    ## TO DO incorporate health
    ##health = data["you"]["health"]
    for food in foods:
        if snek_dist(square, food) < (1/2)*data['board']["width"]:
            foodDist = BFS_dist(square, food, maxBFSDist, data)
            if foodDist == 0:
                score = score + 5
            else:
                score = score + 4/snek_dist(square, food)

    return score

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    color = "#6B5B95"

    return start_response(color)


@bottle.post('/move')
def move():
    data = bottle.request.json

    dangerSquares = danger_squares(data)
    currentSquare = data['you']['body'][0]    ##my head

    safeMoves = []
    directions = ['up', 'down', 'left', 'right']
    for move in directions:
        if one_move(currentSquare, move) not in dangerSquares:
            safeMoves.append(move)
    
    if len(safeMoves) == 0:
        direction = random.choice(directions)    # when there are no safe moves, chaos ensues
    elif len(safeMoves) == 1:
        direction = safeMoves[0]                 # take the only safe move if that's the only choice!
    elif len(safeMoves) > 1:
        direction = safeMoves[0]
        for move in safeMoves:
            if square_score(one_move(currentSquare, move), data) > \
            square_score(one_move(currentSquare, direction), data):
                direction = move
               
                
    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()



if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )

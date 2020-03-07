import json
import os
import random
import bottle

from api import ping_response, start_response, move_response, end_response

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
        
    for width in range(data['board']["width"]):
        dangerSquares.append({"width":width, "length":-1})
        dangerSquares.append({"width":width, "length":data['board']["length"]})
        
    for length in range(data['board']["length"]):
        dangerSquares.append({"width":-1, "length":length})
        dangerSquares.append({"width":data['board']["width"], "length":length})
    
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
    for snek in scarySneks:
        if snek_dist(square, snek[0]) == 1:
            score = score - 4
        else:
            score = score + 2/(snek_dist(square, snek[0]))**2
    for snek in yummySneks:
        if snek_dist(square, snek[0]) == 0:
            score = score - 4 
        elif snek_dist(square, snek[0]) == 1:
            score = score + 3
        else:
            score = score + 2/(snek_dist(square, snek[0]))**2
    for food in foods:
        if snek_dist(square, food) == 0:
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

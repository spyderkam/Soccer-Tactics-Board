#!/user/bin/env python3

__author__ = "Claude 3.5 Sonnet V2"

from flask import Flask, Response, render_template_string, request
from flask_socketio import SocketIO, emit
from main import SCREEN, main, BLUE_TEAM, RED_TEAM, BALL_POS, WIDTH, HEIGHT, draw_player, WHITE, triangle_points, Shape
import base64
import io
import os
import pygame
import json

app = Flask(__name__)
socketio = SocketIO(app)

# Read the HTML file
with open('tactics_board.html', 'r', encoding='utf-8') as file:
  HTML_TEMPLATE = file.read()

show_numbers = False
show_ball = False
show_triangle = False

@app.route('/')
def home():
  return render_template_string(HTML_TEMPLATE)

@socketio.on('check_click')
def check_click(data):
  global BLUE_TEAM, RED_TEAM, triangle_points, BALL_POS, show_ball
  x, y = data['x'], data['y']
    
  # Check if ball is clicked first when visible
  if show_ball and ((x - BALL_POS[0])**2 + (y - BALL_POS[1])**2)**0.5 < 15:  # Matches player click detection radius
    emit('player_selected', {'team': 'ball', 'index': 0})
    return
            
  for i, pos in enumerate(BLUE_TEAM):
    if ((x - pos[0])**2 + (y - pos[1])**2)**0.5 < 15:
      emit('player_selected', {'team': 'blue', 'index': i})
      if len(triangle_points) < 3:
        triangle_points.append(BLUE_TEAM[i])
        update_board()
      return
            
  for i, pos in enumerate(RED_TEAM):
    if ((x - pos[0])**2 + (y - pos[1])**2)**0.5 < 15:
      emit('player_selected', {'team': 'red', 'index': i})
      if len(triangle_points) < 3:
        triangle_points.append(RED_TEAM[i])
        update_board()
      return

@socketio.on('move_player')
def move_player(data):
  global BLUE_TEAM, RED_TEAM, BALL_POS
  x, y = data['x'], data['y']
  team = data['team']
  index = data['index']
    
  global triangle_points
  new_pos = [x, y]
    
  if team == 'ball':
    BALL_POS[0] = x
    BALL_POS[1] = y
  elif team == 'blue':
    old_pos = BLUE_TEAM[index]
    BLUE_TEAM[index] = new_pos
    if old_pos in triangle_points:
      triangle_points[triangle_points.index(old_pos)] = new_pos
  else:
    old_pos = RED_TEAM[index]
    RED_TEAM[index] = new_pos
    if old_pos in triangle_points:
      triangle_points[triangle_points.index(old_pos)] = new_pos
    
  update_board()

@socketio.on('toggle_ball')
def toggle_ball():
  global show_ball
  show_ball = not show_ball
  update_board()

@socketio.on('toggle_numbers')
def toggle_numbers():
  global show_numbers
  show_numbers = not show_numbers
  update_board()

@socketio.on('toggle_triangle')
def toggle_triangle_handler():
  global show_triangle, triangle_points
  if len(triangle_points) == 3:
    show_triangle = not show_triangle
  else:
    triangle_points.clear()
    show_triangle = False
  update_board()

@socketio.on('reset_triangle')
def reset_triangle():
  global triangle_points, show_triangle
  triangle_points.clear()
  show_triangle = False
  update_board()

@socketio.on('reset_board')
def reset_board():
  global BLUE_TEAM, RED_TEAM, BALL_POS, triangle_points, show_triangle
  from main import ORIGINAL_BLUE, ORIGINAL_RED
  BLUE_TEAM[:] = [pos[:] for pos in ORIGINAL_BLUE]
  RED_TEAM[:] = [pos[:] for pos in ORIGINAL_RED]
  BALL_POS[:] = [WIDTH//2, HEIGHT//2]
  triangle_points.clear()
  show_triangle = False
  update_board()

def update_board():
  global show_numbers, show_ball, show_triangle
  SCREEN.fill((34, 139, 34))
  pygame.draw.rect(SCREEN, WHITE, (80, 60, WIDTH-160, HEIGHT-120), 2)
  pygame.draw.line(SCREEN, WHITE, (WIDTH//2, 60), (WIDTH//2, HEIGHT-60), 2)
  pygame.draw.circle(SCREEN, WHITE, (WIDTH//2, HEIGHT//2), 85, 2)
  pygame.draw.circle(SCREEN, WHITE, (WIDTH//2, HEIGHT//2), 6)
  pygame.draw.rect(SCREEN, WHITE, (80, HEIGHT//2-240, 240, 480), 2)          # Left penalty area
  pygame.draw.rect(SCREEN, WHITE, (WIDTH-320, HEIGHT//2-240, 240, 480), 2)   # Right penalty area
  pygame.draw.rect(SCREEN, WHITE, (80, HEIGHT//2-90, 72, 180), 2)            # Left goal area
  pygame.draw.rect(SCREEN, WHITE, (WIDTH-152, HEIGHT//2-90, 72, 180), 2)     # Right goal area

  for i, pos in enumerate(BLUE_TEAM, 1):
    draw_player(SCREEN, pos, (0, 0, 255), i, show_numbers)
  for i, pos in enumerate(RED_TEAM, 1):
    draw_player(SCREEN, pos, (255, 0, 0), i, show_numbers)

  if show_ball:
    pygame.draw.circle(SCREEN, (0, 0, 0), BALL_POS, 15)
        
  if show_triangle and len(triangle_points) == 3:
    Shape().draw_triangle1(SCREEN, triangle_points)

  buffer = io.BytesIO()
  pygame.image.save(SCREEN, buffer, 'PNG')
  buffer.seek(0)
  base64_image = base64.b64encode(buffer.getvalue()).decode()
  emit('board_update', {'image': base64_image}, broadcast=True)

if __name__ == '__main__':
  os.environ['SDL_VIDEODRIVER'] = 'dummy'
  pygame.init()
  socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)
  

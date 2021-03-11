import time
import asyncio
import curses

from random import randint, choice, uniform
from itertools import cycle
from animation.fire_animation import fire
from animation.curses_tools import draw_frame, read_controls, get_frame_size
from animation.space_garbage import fly_garbage
from physics import update_speed
from animation.obstacles import *
from animation.game_over import show_gameover, GAME_OVER_LABEL
from animation.explosion import explode
from game_scenario import *


GAME_TIC_DURATION_SEC = 0.05
GAME_YEAR_IN_SEC = 1.5
LABEL_CLEAR_TOOL = "                                      "
year = 1957
coroutines = []
obstacles = []
obstacles_in_last_collisions = []

async def sleep(tics=1):
  for i in range(randint(0, tics)):
    await asyncio.sleep(0)

def get_frames(file_paths):
  frames = []
  for filepath in file_paths:
    with open(filepath) as frame_file:
    	frames.append(frame_file.read())
  return frames

def init_ship():
  file_paths = [
  		'animation/rocket_frame_1.txt', 
  		'animation/rocket_frame_2.txt'
  ]
  return get_frames(file_paths)


def init_all_the_garbage():
  file_paths = [
      'animation/garbage/duck.txt',
      'animation/garbage/trash_small.txt',
      'animation/garbage/trash_large.txt',
      'animation/garbage/lamp.txt',
      'animation/garbage/trash_xl.txt',
      'animation/garbage/hubble.txt',
  ]
  return get_frames(file_paths)


async def generate_obstacles(canvas, max_width):
  # генерирует мусор и помещает его куда надо

  global year
  global coroutines
  global obstacles
  global obstacles_in_last_collisions

  garbage_frames = init_all_the_garbage()

  while not get_garbage_delay_tics(year):
  	await sleep(1)

  while True:
    await sleep(get_garbage_delay_tics(year))
    garbage_frame = choice(garbage_frames)
    rows_size, cols_size = get_frame_size(garbage_frame)
    obst = Obstacle(0, randint(1,  max_width), rows_size, cols_size)
    obstacles.append(obst)
    coroutines.append(fly_garbage(canvas, obst, garbage_frame, obstacles, obstacles_in_last_collisions, speed=uniform(0.5, 2)))


async def fill_orbit_with_garbage(canvas, max_width):
    global year
    global coroutines

    coroutines.append(generate_obstacles(canvas, max_width))

    tics_count = 0
    while True:
        tics_count += 1
        if tics_count * GAME_TIC_DURATION_SEC == GAME_YEAR_IN_SEC:
            year += 1
            tics_count = 0
        await sleep(1)


async def blink(canvas, row, column, symbol='*'):
    while True:

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(tics=30)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(tics=10)

        canvas.addstr(row, column, symbol)
        await sleep(tics=8)
   
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(tics=3)

        canvas.addstr(row, column, symbol)
        await sleep(tics=2)


async def animate_spaceship(canvas, ship_states, max_row, max_col):
  mid_row, mid_column = max_row // 2, max_col // 2

  row, column = mid_row, mid_column
  ship_height, ship_width = get_frame_size(ship_states[0])

  row_speed_coef = col_speed_coef = 0

  global coroutines
  global year

  for state in cycle(ship_states):
    dy, dx, spaced = read_controls(canvas)
    if spaced and year >= 2020:
      coroutines.append(fire(
                            canvas, 
                            start_row=row, 
                            start_column=column+ship_width//2, 
                            obstacles_list=obstacles, 
                            destroyed_list=obstacles_in_last_collisions
                        )
      )
    row_speed_coef, col_speed_coef = update_speed(row_speed_coef, col_speed_coef, dy, dx)
    row =    fit_coord(row, dy, max_row, row_speed_coef, ship_height)
    column = fit_coord(column, dx, max_col, col_speed_coef, ship_width)
    
    row += row_speed_coef
    column += col_speed_coef 

    draw_frame(canvas, row, column, state)
    await sleep(tics=2)
    draw_frame(canvas, row, column, state, True)

    for obst in obstacles:
      if obst.has_collision(obj_corner_row=row, obj_corner_column=column, obj_size_rows=ship_height, obj_size_columns=ship_width):
        gameover_frame_size = get_frame_size(GAME_OVER_LABEL)
        obstacles.remove(obst)
        await explode(canvas, center_row=row + ship_height // 2, center_column=column + ship_width // 2)
        coroutines.append(show_gameover(canvas, mid_row-gameover_frame_size[0]//2, mid_column-gameover_frame_size[1]//2))
        return


def fit_coord(current_coord, delta, max_val, coef, obj_axis_size):
  """
    подгоняет координаты так, чтобы корабль 
    мог приближаться к краям поля вплотную
  """
  new_coord = current_coord + int(coef * delta)
  if 1 <= new_coord < max_val - obj_axis_size:
    return new_coord
  if new_coord < 1:
    return 1
  return max_val - obj_axis_size - 1

def draw(canvas):
  stars_num = randint(25, 50)
  height, width = canvas.getmaxyx()

  min_height = 1
  min_width = 1
  max_height = height - 1
  max_width = width - 1

  global year
  global coroutines
  global GAME_TIC_DURATION_SEC
  coroutines = [blink(canvas, randint(min_height,max_height), randint(min_width,max_width), choice('+*.:')) for i in range(stars_num)]
  coroutines.append(animate_spaceship(canvas, init_ship(), height, width))

  # garbage
  coroutines.append(fill_orbit_with_garbage(canvas, max_width))
  #coroutines.append(generate_obstacles(canvas, MAX_WIDTH))

  curses.curs_set(False)
  canvas.nodelay(True)
  canvas.border()

  last_year = year

  while coroutines:
    for coroutine in coroutines.copy():
      try:
        coroutine.send(None)
      except StopIteration:
        coroutines.remove(coroutine)
    canvas.refresh()
    time.sleep(GAME_TIC_DURATION_SEC)
    canvas.border()

    new_win = canvas.derwin(int(height*0.93), width - int(width*0.29))
    new_win.border()

    if PHRASES.get(year):
        last_year = year
        new_win.addstr(1, 1, LABEL_CLEAR_TOOL)
    new_win.addstr(1, 1, f"{str(year)} {PHRASES.get(last_year)}")


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

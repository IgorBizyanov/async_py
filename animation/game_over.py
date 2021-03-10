import asyncio
from .curses_tools import draw_frame


GAME_OVER_LABEL = """
 __          __              _____   _______   ______   _____  
 \ \        / /     /\      / ____| |__   __| |  ____| |  __ \ 
  \ \  /\  / /     /  \    | (___      | |    | |__    | |  | |
   \ \/  \/ /     / /\ \    \___ \     | |    |  __|   | |  | |
    \  /\  /     / ____ \   ____) |    | |    | |____  | |__| |
     \/  \/     /_/    \_\ |_____/     |_|    |______| |_____/ 
                                                               
"""

def get_gameover_label():
  return GAME_OVER_LABEL

async def show_gameover(canvas, row, col):
  dy = -1
  while True:
    draw_frame(canvas, start_row=row+dy, start_column=col, text=GAME_OVER_LABEL)
    for i in range(8):
      await asyncio.sleep(0)
    draw_frame(canvas, start_row=row+dy, start_column=col, text=GAME_OVER_LABEL, negative=True)
    dy *= -1
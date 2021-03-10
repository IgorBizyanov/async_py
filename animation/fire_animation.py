import asyncio
import curses
from .explosion import *


async def fire(canvas, start_row, start_column, obstacles_list, destroyed_list, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obst in obstacles_list:
            if obst.has_collision(row, column):
                destroyed_list.append(obst)
                obstacles_list.remove(obst)
                await explode(canvas, center_row=obst.row + obst.rows_size // 2, center_column=obst.column + obst.columns_size // 2)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

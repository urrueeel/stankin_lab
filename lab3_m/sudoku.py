"""Правила судоку, генерация задач и работа с сохранениями."""

import json
import random
import tempfile
from pathlib import Path


LEVELS = {"Легкая": 40, "Средняя": 34, "Сложная": 28}


def validate_grid(grid):
    if not isinstance(grid, list) or len(grid) != 9:
        raise ValueError("В поле должно быть 9 строк.")
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("В строке должно быть 9 клеток.")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("Клетки должны содержать целые числа от 0 до 9.")


def conflicts(grid):
    """Вернуть координаты всех заполненных клеток с повторяющимися числами."""
    result = set()
    groups = [[(r, c) for c in range(9)] for r in range(9)]
    groups += [[(r, c) for r in range(9)] for c in range(9)]
    groups += [
        [(r + dr, c + dc) for dr in range(3) for dc in range(3)]
        for r in range(0, 9, 3) for c in range(0, 9, 3)
    ]
    for group in groups:
        for value in range(1, 10):
            cells = [(r, c) for r, c in group if grid[r][c] == value]
            if len(cells) > 1:
                result.update(cells)
    return result


def solutions(grid, limit=2):
    """Искать до limit решений, выбирая клетку с минимумом кандидатов."""
    validate_grid(grid)
    if conflicts(grid):
        return []
    board = [row[:] for row in grid]
    found = []

    def search():
        best = None
        options = None
        for r in range(9):
            for c in range(9):
                if board[r][c]:
                    continue
                used = set(board[r]) | {board[i][c] for i in range(9)}
                used |= {
                    board[i][j]
                    for i in range(r // 3 * 3, r // 3 * 3 + 3)
                    for j in range(c // 3 * 3, c // 3 * 3 + 3)
                }
                candidates = set(range(1, 10)) - used
                if not candidates:
                    return
                if options is None or len(candidates) < len(options):
                    best, options = (r, c), candidates
        if best is None:
            found.append([row[:] for row in board])
            return
        r, c = best
        for value in sorted(options):
            board[r][c] = value
            search()
            board[r][c] = 0
            if len(found) >= limit:
                break

    search()
    return found


def generate(level="Легкая", rng=None):
    if level not in LEVELS:
        raise ValueError("Неизвестная сложность.")
    rng = rng or random.Random()

    def shuffled(values):
        return rng.sample(list(values), len(values))

    # Перестановки внутри полос и самих полос сохраняют правила судоку.
    rows = [g * 3 + r for g in shuffled(range(3)) for r in shuffled(range(3))]
    cols = [g * 3 + c for g in shuffled(range(3)) for c in shuffled(range(3))]
    numbers = shuffled(range(1, 10))
    answer = [
        [numbers[(r * 3 + r // 3 + c) % 9] for c in cols] for r in rows
    ]
    puzzle = [row[:] for row in answer]
    filled = 81
    for index in shuffled(range(81)):
        if filled <= LEVELS[level]:
            break
        r, c = divmod(index, 9)
        old = puzzle[r][c]
        puzzle[r][c] = 0
        if len(solutions(puzzle)) == 1:
            filled -= 1
        else:
            puzzle[r][c] = old
    return puzzle, answer


def validate_game(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int:
        raise ValueError("Неверный формат сохранения.")
    if data["version"] != 1:
        raise ValueError("Версия сохранения не поддерживается.")
    if data.get("level") not in LEVELS:
        raise ValueError("Неверная сложность.")
    puzzle, board = data.get("puzzle"), data.get("board")
    validate_grid(puzzle)
    validate_grid(board)
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] and puzzle[r][c] != board[r][c]:
                raise ValueError("В сохранении изменены исходные числа.")
    found = solutions(puzzle)
    if len(found) != 1:
        raise ValueError("Исходная задача должна иметь ровно одно решение.")
    return puzzle, board, data["level"], found[0]


def load_game(path):
    # Ограничение защищает от случайного открытия большого постороннего файла.
    with Path(path).open("r", encoding="utf-8") as stream:
        content = stream.read(100_001)
    if len(content) > 100_000:
        raise ValueError("Файл сохранения слишком большой.")
    try:
        return validate_game(json.loads(content))
    except (TypeError, RecursionError) as error:
        raise ValueError("Неверная структура сохранения.") from error


def save_game(path, puzzle, board, level):
    data = {"version": 1, "level": level, "puzzle": puzzle, "board": board}
    validate_game(data)
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
        # Сначала дописываем временный файл, затем заменяем сохранение.
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

from __future__ import annotations


def bresenham_line(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    x0, y0 = start
    x1, y1 = end
    points: list[tuple[int, int]] = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((x0, y0))
        if (x0, y0) == (x1, y1):
            break
        doubled_error = 2 * err
        if doubled_error > -dy:
            err -= dy
            x0 += sx
        if doubled_error < dx:
            err += dx
            y0 += sy

    return points

"""Painters for synthetic educational-video fixtures.

Each painter draws one kind of visual onto a BGR frame. They are used
by ``conftest.py`` to build videos with *known* content: diagrams,
talking heads, whiteboards, repeated slides, and so on.
"""

from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np

# Common canvas size for fixtures (small enough for fast tests).
WIDTH = 640
HEIGHT = 360

Painter = Callable[[np.ndarray], np.ndarray]


def _canvas(color: tuple[int, int, int]) -> np.ndarray:
    return np.full((HEIGHT, WIDTH, 3), color, dtype=np.uint8)


# ----------------------------------------------------------------------
# Diagram-like painters (edges + long straight lines + text detail)
# ----------------------------------------------------------------------


def paint_flowchart(frame: np.ndarray) -> np.ndarray:
    """A classic boxes-and-arrows flowchart."""
    canvas = _canvas((245, 245, 245))

    boxes = [(60, 60, 240, 120), (340, 60, 520, 120), (200, 240, 400, 310)]
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (30, 30, 30), 2)
        cv2.putText(
            canvas,
            "Step",
            (x1 + 25, (y1 + y2) // 2 + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 20, 20),
            2,
        )

    cv2.arrowedLine(canvas, (240, 90), (340, 90), (30, 30, 30), 2)
    cv2.arrowedLine(canvas, (280, 120), (280, 240), (30, 30, 30), 2)
    cv2.arrowedLine(canvas, (320, 120), (320, 240), (30, 30, 30), 2)
    return canvas


def paint_bar_chart(frame: np.ndarray) -> np.ndarray:
    """A bar chart with axes, gridlines and labeled bars."""
    canvas = _canvas((250, 250, 250))

    # Axes.
    cv2.line(canvas, (80, 40), (80, 300), (0, 0, 0), 2)
    cv2.line(canvas, (80, 300), (600, 300), (0, 0, 0), 2)

    # Gridlines.
    for y in range(100, 300, 50):
        cv2.line(canvas, (80, y), (600, y), (200, 200, 200), 1)

    # Bars.
    for index, height in enumerate([80, 160, 120, 220, 180]):
        x = 120 + index * 90
        cv2.rectangle(
            canvas,
            (x, 300 - height),
            (x + 50, 300),
            (60, 60, 200),
            -1,
        )
        cv2.putText(
            canvas,
            "Q" + str(index + 1),
            (x + 5, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
        )
    return canvas


def paint_table(frame: np.ndarray) -> np.ndarray:
    """A structured table with grid lines and text cells."""
    canvas = _canvas((255, 255, 255))

    rows, cols = 5, 4
    left, top = 80, 60
    cell_w, cell_h = 120, 48

    for row in range(rows + 1):
        y = top + row * cell_h
        cv2.line(
            canvas,
            (left, y),
            (left + cols * cell_w, y),
            (0, 0, 0),
            2,
        )
    for col in range(cols + 1):
        x = left + col * cell_w
        cv2.line(
            canvas,
            (x, top),
            (x, top + rows * cell_h),
            (0, 0, 0),
            2,
        )

    for row in range(rows):
        for col in range(cols):
            x = left + col * cell_w + 10
            y = top + row * cell_h + 32
            cv2.putText(
                canvas,
                f"R{row}C{col}",
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (40, 40, 40),
                1,
            )
    return canvas


def paint_formula_slide(frame: np.ndarray) -> np.ndarray:
    """A math slide: formulas with fraction bars and a radical."""
    canvas = _canvas((252, 252, 252))

    cv2.putText(
        canvas,
        "E = mc^2",
        (150, 120),
        cv2.FONT_HERSHEY_DUPLEX,
        1.6,
        (10, 10, 10),
        3,
    )
    cv2.putText(
        canvas,
        "a^2 + b^2 = c^2",
        (110, 220),
        cv2.FONT_HERSHEY_DUPLEX,
        1.4,
        (10, 10, 10),
        3,
    )
    # A real fraction bar and radical sign are long straight segments.
    cv2.line(canvas, (330, 290), (560, 290), (10, 10, 10), 2)
    cv2.putText(canvas, "b^2 - 4ac", (360, 282),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(canvas, "2a", (430, 322),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.line(canvas, (340, 265), (350, 300), (10, 10, 10), 2)
    cv2.line(canvas, (350, 300), (358, 245), (10, 10, 10), 2)
    return canvas


# ----------------------------------------------------------------------
# Non-diagram painters (talking heads, boards, plain scenes)
# ----------------------------------------------------------------------


def paint_talking_head(frame: np.ndarray) -> np.ndarray:
    """A webcam-style frame: smooth background, blurred face oval."""
    canvas = _canvas((150, 130, 110))  # warm beige background

    # Soft, organic head shape.
    center = (320, 170)
    cv2.ellipse(canvas, center, (95, 130), 0, 0, 360, (110, 160, 220), -1)
    cv2.ellipse(canvas, (320, 150), (28, 14), 0, 0, 360, (90, 90, 90), -1)
    cv2.ellipse(canvas, (320, 150), (28, 14), 0, 0, 360, (90, 90, 90), -1)
    # Blurred overlay keeps the region smooth, like camera bokeh.
    canvas = cv2.GaussianBlur(canvas, (21, 21), 0)
    # Small dark eyes/mouth (low edge energy after blur).
    cv2.ellipse(canvas, (295, 140), (8, 5), 0, 0, 360, (30, 30, 30), -1)
    cv2.ellipse(canvas, (345, 140), (8, 5), 0, 0, 360, (30, 30, 30), -1)
    cv2.ellipse(canvas, (320, 210), (16, 6), 0, 0, 360, (60, 40, 40), -1)
    return canvas


def paint_whiteboard(frame: np.ndarray) -> np.ndarray:
    """A lightly used whiteboard: faint noise, almost no long lines."""
    canvas = _canvas((240, 240, 240))
    noise = np.random.default_rng(7).normal(0, 3, canvas.shape)
    canvas = np.clip(canvas.astype(np.float32) + noise, 0, 255).astype(
        np.uint8
    )
    return canvas


def paint_blank(frame: np.ndarray) -> np.ndarray:
    """A fully black frame (rejected before scoring anyway)."""
    return np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

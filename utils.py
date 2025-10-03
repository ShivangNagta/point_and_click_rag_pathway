def click_in_bounds(x, y, window) -> bool:
    return (0 <= x and x <= window.width) and (0 <= y and y <= window.height)
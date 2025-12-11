
def format_str_with_color(str, color):
    if color == "red": return f"\033[{31}m{str}\033[0m"
    if color == "green": return f"\033[{32}m{str}\033[0m"
    if color == "yellow":return f"\033[{33}m{str}\033[0m"
    if color == "blue": return f"\033[{34}m{str}\033[0m"
    if color == "orange": return f"\033[38;2;255;140;0m{str}\033[0m"
    return str

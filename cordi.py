import matplotlib.pyplot as plt
import re
from docx import Document

# =============================
# SETTINGS
# =============================

word = '''Vinayak Handa'''

s=2.5
start_x = 0        # cm
baseline_y = 3     # cm
scale = 0.04*s       # size multiplier
spacing = 0      # space between letters (cm)
vertical_offset = -1*s
horizontal_offset = 0.2

width = 10
height = 10

ardi=[]

# =============================
# LOAD FONT FILE
# =============================

with open("cursive.h", "r", encoding="utf-8") as f:
    content = f.read()

# =============================
# FUNCTION: LOAD ONE LETTER
# =============================

def get_glyph_points(ch):
    glyph_number = str(ord(ch) - 31)
    # print(glyph_number)

    pattern = re.search(
        rf"static const char cursive_{glyph_number}\[\d+\]\s*=\s*\{{(.*?)\}};",
        content,
        re.S
    )

    if not pattern:
        # print(f"Glyph for '{ch}' not found!")
        return []

    numbers = list(map(int, re.findall(r"-?\d+", pattern.group(1))))

    points = []
    for i in range(0, len(numbers), 2):
        if i + 1 < len(numbers):
            points.append((numbers[i], numbers[i+1]))

    return points

# =============================
# FUNCTION: DRAW LETTER
# =============================

def draw_letter(ax, ch, start_x, baseline_y, scale, spacing):

    points = get_glyph_points(ch)
    ardi.append((-1,-1))

    x_vals = []
    y_vals = []

    pen_x = start_x
    max_x = 0
    i = 0
    while i < len(points):

        x, y = points[i]

        # Stroke break
        if x == -1 and y == -1:
            ardi.append((-1, -1))
            x_vals = []
            y_vals = []

            # Add next coordinate immediately after (-1,-1)
            if i + 1 < len(points):
                nx, ny = points[i + 1]

                x_scaled = horizontal_offset + pen_x + nx * scale
                y_scaled = baseline_y + vertical_offset + ny * scale

                x_vals.append(x_scaled)
                y_vals.append(y_scaled)

                if nx > max_x:
                    max_x = nx

                ardi.append((round(x_scaled, 3), round(y_scaled, 3)))

                ardi.append((-2, -2))

                i += 1      # Skip the next point since we've already handled it

        else:

            x_scaled = horizontal_offset + pen_x + x * scale
            y_scaled = baseline_y + vertical_offset + y * scale

            x_vals.append(x_scaled)
            y_vals.append(y_scaled)

            if x > max_x:
                max_x = x
            
            ardi.append((round(x_scaled, 3), round(y_scaled, 3)))

            if i==0:
                ardi.append((-2,-2))



        i += 1

    pos=pen_x + max_x * scale + spacing
    ardi.append((-1,-1))
    ardi.append("done")
    
    return pos


# =============================
# DRAW 15x15 RULED SHEET
# =============================
fig, ax = plt.subplots(figsize=(6, 6))

# Horizontal 1 cm lines
for y in range(0, height + 1):
    ax.plot([0, width], [y, y], color='blue', linewidth=0.5)

# Border
ax.plot([0, width, width, 0, 0],
        [0, 0, height, height, 0],
        color='black')

# Fixed scale
ax.set_xlim(0, width)
ax.set_ylim(0, height)
ax.set_aspect('equal')   # TRUE fixed scale (1cm = 1cm)
ax.invert_yaxis()

ax.set_xlabel("cm")
ax.set_ylabel("cm")
ax.set_title("Cursive CNC Writing Preview")

# ==========================================================================================================================================

def ardi_to_relative(ardi):
    relative = []

    prev = None

    for item in ardi:

        if item == (-1, -1):
            relative.append("UP")

        elif item == (-2, -2):
            relative.append("DOWN")

        elif item == "done":
            continue

        else:
            if prev is None:
                # First coordinate is absolute
                relative.append(item)
            else:
                dx = round(item[0] - prev[0], 3)
                dy = round(item[1] - prev[1], 3)
                if (dx,dy)!=(0,0):
                    relative.append((dx, dy))

            prev = item

    return relative

def plot_relative(ax, moves):
    x = 0.0
    y = 0.0

    pen_down = False
    xs = []
    ys = []

    for move in moves:

        if move == "UP":
            if len(xs) > 1:
                ax.plot(xs, ys, 'k', linewidth=1)
            xs = []
            ys = []
            pen_down = False

        elif move == "DOWN":
            xs = [x]
            ys = [y]
            pen_down = True

        else:
            dx, dy = move
            x += dx
            y += dy

            if pen_down:
                xs.append(x)
                ys.append(y)

    # Draw the last stroke
    if len(xs) > 1:
        ax.plot(xs, ys, 'k', linewidth=1)

def ref(moves):
    out = []
    pen = "UP"          # Initial state

    for item in moves:

        if item == "UP":
            if pen == "UP":
                continue            # Already up
            out.append("UP")
            pen = "UP"

        elif item == "DOWN":
            if pen == "DOWN":
                continue            # Already down
            out.append("DOWN")
            pen = "DOWN"

        else:
            out.append(item)

    return out

# =============================
# WRITE WORD
# =============================

x = start_x
for ch in word:
    if ch == " ":
        # Lift pen and move to next word
        ardi.append((-1, -1))
        x += 0.5        # Adjust word spacing
        continue
    elif ch == "\n":
        # New line
        ardi.append((-1, -1))
        baseline_y += 2
        x = start_x
        continue

    x = draw_letter(ax, ch, x, baseline_y, scale, spacing)

n1=ref(ardi_to_relative(ardi))
print(n1)
plot_relative(ax,n1)

def take():
    return n1

plt.show()

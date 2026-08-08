import re
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =============================
# LOAD FONT FILE
# =============================
FONT_FILE = "cursive.h"
try:
    with open(FONT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    content = ""


def get_glyph_points(ch):
    glyph_number = str(ord(ch) - 31)
    pattern = re.search(
        rf"static const char cursive_{glyph_number}\[\d+\]\s*=\s*\{{(.*?)\}};",
        content,
        re.S,
    )

    if not pattern:
        return []

    numbers = list(map(int, re.findall(r"-?\d+", pattern.group(1))))
    points = []
    for i in range(0, len(numbers), 2):
        if i + 1 < len(numbers):
            points.append((numbers[i], numbers[i + 1]))

    return points


def draw_letter(
    ch, start_x, baseline_y, scale, spacing, vertical_offset, horizontal_offset, ardi
):
    points = get_glyph_points(ch)
    ardi.append((-1, -1))

    x_vals = []
    y_vals = []

    pen_x = start_x
    max_x = 0
    i = 0
    while i < len(points):
        x, y = points[i]

        if x == -1 and y == -1:
            ardi.append((-1, -1))
            x_vals = []
            y_vals = []

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
                i += 1
        else:
            x_scaled = horizontal_offset + pen_x + x * scale
            y_scaled = baseline_y + vertical_offset + y * scale

            x_vals.append(x_scaled)
            y_vals.append(y_scaled)

            if x > max_x:
                max_x = x

            ardi.append((round(x_scaled, 3), round(y_scaled, 3)))

            if i == 0:
                ardi.append((-2, -2))

        i += 1

    pos = pen_x + max_x * scale + spacing
    ardi.append((-1, -1))
    ardi.append("done")

    return pos


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
                relative.append(item)
            else:
                dx = round(item[0] - prev[0], 3)
                dy = round(item[1] - prev[1], 3)
                if (dx, dy) != (0, 0):
                    relative.append((dx, dy))
            prev = item

    return relative


def ref(moves):
    out = []
    pen = "UP"

    for item in moves:
        if item == "UP":
            if pen == "UP":
                continue
            out.append("UP")
            pen = "UP"
        elif item == "DOWN":
            if pen == "DOWN":
                continue
            out.append("DOWN")
            pen = "DOWN"
        else:
            out.append(item)

    return out


def plot_relative(ax, moves):
    x = 0.0
    y = 0.0
    pen_down = False
    xs = []
    ys = []

    for move in moves:
        if move == "UP":
            if len(xs) > 1:
                ax.plot(xs, ys, "k", linewidth=1)
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

    if len(xs) > 1:
        ax.plot(xs, ys, "k", linewidth=1)


# =============================
# TKINTER APPLICATION
# =============================


class CursiveGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Cursive CNC Generator")
        self.root.geometry("1100x700")

        if not content:
            messagebox.showwarning(
                "Missing File",
                f"Could not find '{FONT_FILE}' in the local directory. Please ensure it is present.",
            )

        # -----------------------------
        # Left Control Panel
        # -----------------------------
        control_frame = ttk.Frame(root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            control_frame, text="Custom Text:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 2))
        self.text_entry = ttk.Entry(control_frame, width=22, font=("Arial", 11))
        self.text_entry.insert(0, "parth")
        self.text_entry.pack(anchor="w", pady=(0, 15))

        ttk.Label(control_frame, text="Size Multiplier (s):").pack(
            anchor="w", pady=(5, 0)
        )
        self.scale_var = tk.DoubleVar(value=2.5)
        self.scale_slider = ttk.Scale(
            control_frame,
            from_=0.5,
            to=5.0,
            variable=self.scale_var,
            orient="horizontal",
        )
        self.scale_slider.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(control_frame, text="Start X (cm):").pack(
            anchor="w", pady=(5, 0)
        )
        self.start_x_var = tk.DoubleVar(value=0.0)
        self.start_x_entry = ttk.Entry(
            control_frame, textvariable=self.start_x_var
        )
        self.start_x_entry.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(control_frame, text="Baseline Y (cm):").pack(
            anchor="w", pady=(5, 0)
        )
        self.baseline_y_var = tk.DoubleVar(value=3.0)
        self.baseline_y_entry = ttk.Entry(
            control_frame, textvariable=self.baseline_y_var
        )
        self.baseline_y_entry.pack(fill=tk.X, pady=(0, 15))

        self.generate_btn = ttk.Button(
            control_frame, text="Generate Preview", command=self.update_plot
        )
        self.generate_btn.pack(fill=tk.X, pady=20)

        # -----------------------------
        # Right Sidebar (Output Coordinates)
        # -----------------------------
        sidebar_frame = ttk.Frame(root, padding="10")
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(
            sidebar_frame,
            text="Output Coordinates:",
            font=("Arial", 10, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        # Text area + Scrollbar container
        txt_container = ttk.Frame(sidebar_frame)
        txt_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(txt_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.coords_text = tk.Text(
            txt_container,
            width=25,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
            wrap=tk.NONE,
        )
        self.coords_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.coords_text.yview)

        # -----------------------------
        # Center Matplotlib Canvas
        # -----------------------------
        self.plot_frame = ttk.Frame(root)
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial Render
        self.update_plot()

    def update_plot(self):
        word = self.text_entry.get()
        s = self.scale_var.get()
        start_x = self.start_x_var.get()
        baseline_y = self.baseline_y_var.get()

        scale = 0.04 * s
        spacing = 0
        vertical_offset = -1 * s
        horizontal_offset = 0.2
        width = 10
        height = 10

        ardi = []

        self.ax.clear()

        # Grid lines
        for y in range(0, height + 1):
            self.ax.plot([0, width], [y, y], color="blue", linewidth=0.5)

        self.ax.plot(
            [0, width, width, 0, 0],
            [0, 0, height, height, 0],
            color="black",
        )

        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect("equal")
        self.ax.invert_yaxis()
        self.ax.set_xlabel("cm")
        self.ax.set_ylabel("cm")
        self.ax.set_title("Cursive CNC Writing Preview")

        curr_x = start_x
        curr_baseline_y = baseline_y

        for ch in word:
            if ch == " ":
                ardi.append((-1, -1))
                curr_x += 0.5
                continue
            elif ch == "\n":
                ardi.append((-1, -1))
                curr_baseline_y += 2
                curr_x = start_x
                continue

            curr_x = draw_letter(
                ch,
                curr_x,
                curr_baseline_y,
                scale,
                spacing,
                vertical_offset,
                horizontal_offset,
                ardi,
            )

        relative_moves = ref(ardi_to_relative(ardi))
        plot_relative(self.ax, relative_moves)
        self.canvas.draw()

        # Update right sidebar coordinates
        self.coords_text.config(state=tk.NORMAL)
        self.coords_text.delete("1.0", tk.END)

        formatted_coords = "\n".join(str(move) for move in relative_moves)
        self.coords_text.insert(tk.END, formatted_coords)
        self.coords_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = CursiveGUI(root)
    root.mainloop()
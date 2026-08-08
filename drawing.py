import tkinter as tk
from tkinter import ttk

# =============================
# TKINTER CUSTOM DRAWING GUI
# =============================


class CustomPenGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Custom Pen Drawing Coordinate Generator")
        self.root.geometry("1100x700")

        # Stores raw strokes: list of point arrays [(x1, y1), (x2, y2), ...]
        self.strokes = []
        self.current_stroke = []

        # -----------------------------
        # Left Control Panel
        # -----------------------------
        control_frame = ttk.Frame(root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            control_frame, text="Drawing Controls", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Scale Factor (Pixels per unit/cm)
        ttk.Label(control_frame, text="Pixels per Unit (cm):").pack(
            anchor="w", pady=(5, 0)
        )
        self.scale_var = tk.DoubleVar(value=50.0)
        self.scale_entry = ttk.Entry(
            control_frame, textvariable=self.scale_var, width=15
        )
        self.scale_entry.pack(anchor="w", pady=(0, 15))

        # Action Buttons
        self.generate_btn = ttk.Button(
            control_frame,
            text="Output Coordinates",
            command=self.output_coordinates,
        )
        self.generate_btn.pack(fill=tk.X, pady=5)

        self.clear_btn = ttk.Button(
            control_frame, text="Clear Canvas", command=self.clear_canvas
        )
        self.clear_btn.pack(fill=tk.X, pady=5)

        # Quick Instructions
        instructions = (
            "Instructions:\n"
            "1. Left-click & drag on canvas to draw.\n"
            "2. Release mouse to end a stroke.\n"
            "3. Click 'Output Coordinates' to generate\n"
            "   relative CNC movement data."
        )
        ttk.Label(
            control_frame,
            text=instructions,
            font=("Arial", 8),
            foreground="gray",
        ).pack(anchor="w", pady=20)

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
        # Center Interactive Canvas
        # -----------------------------
        self.canvas_frame = ttk.Frame(root, padding="10")
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.canvas_frame, bg="white", cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Mouse Event Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    # -----------------------------
    # Drawing Handlers
    # -----------------------------
    def on_press(self, event):
        self.current_stroke = [(event.x, event.y)]

    def on_drag(self, event):
        if self.current_stroke:
            x_prev, y_prev = self.current_stroke[-1]
            self.canvas.create_line(
                x_prev, y_prev, event.x, event.y, fill="black", width=2
            )
            self.current_stroke.append((event.x, event.y))

    def on_release(self, event):
        if self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = []

    def clear_canvas(self):
        self.canvas.delete("all")
        self.strokes = []
        self.coords_text.config(state=tk.NORMAL)
        self.coords_text.delete("1.0", tk.END)
        self.coords_text.config(state=tk.DISABLED)

    # -----------------------------
    # Relative Movement Calculation
    # -----------------------------
    def generate_relative_moves(self):
        try:
            scale = float(self.scale_var.get())
            if scale <= 0:
                scale = 1.0
        except ValueError:
            scale = 50.0

        relative_moves = []
        pen_is_down = False
        prev_pt = None

        for stroke in self.strokes:
            if not stroke:
                continue

            if pen_is_down:
                relative_moves.append("UP")
                pen_is_down = False

            for i, (x, y) in enumerate(stroke):
                scaled_x = x / scale
                scaled_y = y / scale

                if i == 0:
                    if prev_pt is None:
                        dx = round(scaled_x, 3)
                        dy = round(scaled_y, 3)
                    else:
                        dx = round(scaled_x - prev_pt[0], 3)
                        dy = round(scaled_y - prev_pt[1], 3)

                    if (dx, dy) != (0, 0):
                        relative_moves.append((dx, dy))

                    relative_moves.append("DOWN")
                    pen_is_down = True
                    prev_pt = (scaled_x, scaled_y)
                else:
                    dx = round(scaled_x - prev_pt[0], 3)
                    dy = round(scaled_y - prev_pt[1], 3)

                    if (dx, dy) != (0, 0):
                        relative_moves.append((dx, dy))
                    prev_pt = (scaled_x, scaled_y)

            relative_moves.append("UP")
            pen_is_down = False

        return relative_moves

    def output_coordinates(self):
        moves = self.generate_relative_moves()

        self.coords_text.config(state=tk.NORMAL)
        self.coords_text.delete("1.0", tk.END)

        formatted_coords = "\n".join(str(move) for move in moves)
        self.coords_text.insert(tk.END, formatted_coords)
        self.coords_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = CustomPenGUI(root)
    root.mainloop()
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FONT_FILE = "cursive.h"
try:
    with open(FONT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    content = ""

try:
    import easyocr
except ImportError:
    easyocr = None

reader = None
reader_error = ""


def init_reader(use_gpu=False):
    global reader, reader_error
    reader_error = ""
    if easyocr is None:
        reader = None
        reader_error = "easyocr is not installed."
        return
    try:
        reader = easyocr.Reader(["en"], gpu=use_gpu)
    except Exception as exc:
        reader_error = str(exc)
        reader = None


if easyocr is not None:
    init_reader(use_gpu=False)
else:
    reader_error = "easyocr is not installed."


# =============================
# Cursive glyph utilities
# =============================

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

    pen_x = start_x
    max_x = 0
    i = 0
    while i < len(points):
        x, y = points[i]

        if x == -1 and y == -1:
            ardi.append((-1, -1))
            if i + 1 < len(points):
                nx, ny = points[i + 1]
                x_scaled = horizontal_offset + pen_x + nx * scale
                y_scaled = baseline_y + vertical_offset + ny * scale
                ardi.append((round(x_scaled, 3), round(y_scaled, 3)))
                ardi.append((-2, -2))
                if nx > max_x:
                    max_x = nx
                i += 1
        else:
            x_scaled = horizontal_offset + pen_x + x * scale
            y_scaled = baseline_y + vertical_offset + y * scale
            ardi.append((round(x_scaled, 3), round(y_scaled, 3)))
            if x > max_x:
                max_x = x
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


class AppHome:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR + Cursive CNC Generator")
        self.root.geometry("1200x760")
        self.root.minsize(1024, 700)

        self.image_photo = None
        self.annotated_photo = None

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.ocr_tab = ttk.Frame(notebook)
        self.cursive_tab = ttk.Frame(notebook)

        notebook.add(self.ocr_tab, text="OCR Image Viewer")
        notebook.add(self.cursive_tab, text="Cursive CNC Preview")

        self._build_ocr_tab()
        self._build_cursive_tab()

        self.status_label = ttk.Label(self.root, text="Ready", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))

    def _build_ocr_tab(self):
        top_frame = ttk.Frame(self.ocr_tab, padding=10)
        top_frame.pack(fill="x", pady=(0, 8))

        self.gpu_var = tk.BooleanVar(value=False)
        self.ocr_status_var = tk.StringVar(value="easyocr available" if easyocr else "easyocr not installed")

        gpu_check = ttk.Checkbutton(
            top_frame,
            text="Use GPU",
            variable=self.gpu_var,
            command=self._update_ocr_status,
        )
        gpu_check.pack(side="left", padx=(0, 10))

        select_button = ttk.Button(
            top_frame,
            text="Select Image",
            command=self.select_and_process_image,
        )
        select_button.pack(side="left")

        ocr_status_label = ttk.Label(top_frame, textvariable=self.ocr_status_var)
        ocr_status_label.pack(side="left", padx=(12, 0))

        content_frame = ttk.Frame(self.ocr_tab, padding=10)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=0)

        image_frame = ttk.LabelFrame(content_frame, text="Image Preview")
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

        self.original_label = ttk.Label(image_frame, text="No image selected", anchor="center")
        self.original_label.pack(fill="both", expand=True, padx=10, pady=10)

        annotated_frame = ttk.LabelFrame(content_frame, text="Annotated OCR Preview")
        annotated_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))

        self.annotated_label = ttk.Label(annotated_frame, text="OCR annotated image will appear here", anchor="center")
        self.annotated_label.pack(fill="both", expand=True, padx=10, pady=10)

        output_frame = ttk.LabelFrame(content_frame, text="OCR Output")
        output_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Arial", 10), height=10)
        self.output_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        if easyocr is None:
            self.output_text.insert(tk.END, "easyocr is not installed. Install it to enable OCR functionality.\n")

    def _build_cursive_tab(self):
        container = ttk.Frame(self.cursive_tab, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        control_frame = ttk.LabelFrame(container, text="Cursive CNC Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=0)

        ttk.Label(control_frame, text="Custom Text (multi-line):", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.text_entry = scrolledtext.ScrolledText(control_frame, width=26, height=6, font=("Arial", 11), wrap=tk.WORD)
        self.text_entry.insert(tk.END, "parth")
        self.text_entry.pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Size Multiplier (s):").pack(anchor="w", pady=(0, 4))
        self.scale_var = tk.DoubleVar(value=2.5)
        self.scale_slider = ttk.Scale(
            control_frame,
            from_=0.5,
            to=5.0,
            variable=self.scale_var,
            orient="horizontal",
        )
        self.scale_slider.pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Start X (cm):").pack(anchor="w", pady=(0, 4))
        self.start_x_var = tk.DoubleVar(value=0.0)
        ttk.Entry(control_frame, textvariable=self.start_x_var).pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Baseline Y (cm):").pack(anchor="w", pady=(0, 4))
        self.baseline_y_var = tk.DoubleVar(value=3.0)
        ttk.Entry(control_frame, textvariable=self.baseline_y_var).pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Vertical Offset (cm):").pack(anchor="w", pady=(0, 4))
        self.vertical_offset_var = tk.DoubleVar(value=-2.5)
        ttk.Entry(control_frame, textvariable=self.vertical_offset_var).pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Horizontal Offset (cm):").pack(anchor="w", pady=(0, 4))
        self.horizontal_offset_var = tk.DoubleVar(value=0.2)
        ttk.Entry(control_frame, textvariable=self.horizontal_offset_var).pack(fill="x", pady=(0, 12))

        ttk.Label(control_frame, text="Letter Spacing (cm):").pack(anchor="w", pady=(0, 4))
        self.spacing_var = tk.DoubleVar(value=0.0)
        ttk.Entry(control_frame, textvariable=self.spacing_var).pack(fill="x", pady=(0, 12))

        self.generate_btn = ttk.Button(
            control_frame,
            text="Generate Preview",
            command=self.update_plot,
        )
        self.generate_btn.pack(fill="x", pady=(10, 0))

        right_frame = ttk.Frame(container)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=0)

        preview_frame = ttk.LabelFrame(right_frame, text="Handwriting Preview")
        preview_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#f9f9f9")
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, preview_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        coordinates_frame = ttk.LabelFrame(right_frame, text="Output Coordinates")
        coordinates_frame.grid(row=1, column=0, sticky="nsew")
        coordinates_frame.columnconfigure(0, weight=1)
        coordinates_frame.rowconfigure(0, weight=1)

        self.coords_text = scrolledtext.ScrolledText(coordinates_frame, wrap=tk.WORD, font=("Consolas", 10), height=10)
        self.coords_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        if not content:
            self.coords_text.insert(tk.END, f"Could not find '{FONT_FILE}'. Cursive preview is disabled until the font file is available.\n")

    def _update_ocr_status(self):
        if easyocr is None:
            self.ocr_status_var.set("easyocr is not installed.")
            return

        if self.gpu_var.get():
            self.ocr_status_var.set("Initializing easyocr with GPU...")
        else:
            self.ocr_status_var.set("Initializing easyocr on CPU...")

        init_reader(use_gpu=self.gpu_var.get())
        if reader is None:
            self.ocr_status_var.set(f"OCR unavailable: {reader_error}")
        else:
            self.ocr_status_var.set("easyocr ready")

    def select_and_process_image(self):
        if easyocr is None:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "easyocr is not installed. Install it to enable OCR.\n")
            return

        self._update_ocr_status()

        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
        )
        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                original_img = img.copy()
                original_img.thumbnail((420, 420))
                self.image_photo = ImageTk.PhotoImage(original_img)
                self.original_label.config(image=self.image_photo, text="")
        except Exception as exc:
            self.original_label.config(image="", text=f"Could not load image:\n{exc}")
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"Could not load image:\n{exc}\n")
            return

        if reader is None:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, f"OCR is unavailable.\n{reader_error}\n")
            self.annotated_label.config(image="", text="OCR unavailable")
            self.annotated_photo = None
            return

        try:
            results = reader.readtext(file_path, detail=1)
            output = "\n".join([item[1] for item in results]) if results else "No text detected."

            annotated_img = Image.open(file_path).copy()
            annotated_img.thumbnail((420, 420))
            draw = ImageDraw.Draw(annotated_img)
            for item in results:
                bbox = item[0]
                points = [(x, y) for x, y in bbox]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                draw.rectangle([min(xs), min(ys), max(xs), max(ys)], outline="red", width=3)

            self.annotated_photo = ImageTk.PhotoImage(annotated_img)
            self.annotated_label.config(image=self.annotated_photo, text="")
        except Exception as exc:
            output = f"Error during OCR:\n{exc}"
            self.annotated_label.config(image="", text="Could not generate annotated preview")
            self.annotated_photo = None

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, output)
        self.status_label.config(text="OCR completed")

    def update_plot(self):
        self.ax.clear()
        self.ax.set_facecolor("#f9f9f9")
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.axis("off")

        text = self.text_entry.get("1.0", tk.END).rstrip()
        if not text:
            messagebox.showwarning("No text", "Please enter some text to generate cursive preview.")
            return

        size_multiplier = self.scale_var.get()
        start_x = self.start_x_var.get()
        baseline_y = self.baseline_y_var.get()
        vertical_offset = self.vertical_offset_var.get()
        horizontal_offset = self.horizontal_offset_var.get()
        spacing = self.spacing_var.get()

        # Match original cursive sizing behavior.
        scale = 0.04 * size_multiplier

        ardi = []
        pen_x = start_x
        pen_baseline = baseline_y

        for ch in text:
            if ch == " ":
                ardi.append((-1, -1))
                pen_x += 0.5
                continue
            if ch == "\n":
                ardi.append((-1, -1))
                pen_baseline += 2.0
                pen_x = start_x
                continue

            pen_x = draw_letter(
                ch,
                pen_x,
                pen_baseline,
                scale,
                spacing,
                vertical_offset,
                horizontal_offset,
                ardi,
            )

        x_points = [item[0] for item in ardi if isinstance(item, tuple)]
        y_points = [item[1] for item in ardi if isinstance(item, tuple)]

        width = max(10, max(x_points, default=0) + 2)
        height = max(8, max(y_points, default=0) + 2)

        for y in range(0, int(height) + 1):
            self.ax.plot([0, width], [y, y], color="#c0c0ff", linewidth=0.6)

        self.ax.plot([0, width, width, 0, 0], [0, 0, height, height, 0], color="black", linewidth=1)
        self.ax.plot([0, width], [baseline_y, baseline_y], color="#c34243", linestyle="--", linewidth=0.8)
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.invert_yaxis()
        self.ax.set_xlabel("cm")
        self.ax.set_ylabel("cm")
        self.ax.set_title("Cursive CNC Writing Preview")

        relative = ardi_to_relative(ardi)
        moves = ref(relative)

        plot_relative(self.ax, moves)
        self.canvas.draw()

        self.coords_text.delete("1.0", tk.END)
        self.coords_text.insert(tk.END, "\n".join(str(item) for item in moves))
        self.status_label.config(text="Cursive preview generated")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppHome(root)
    root.mainloop()

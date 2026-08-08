import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk, ImageDraw

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


def select_and_process_image():
    use_gpu = gpu_var.get()
    init_reader(use_gpu=use_gpu)

    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
    )

    if not file_path:
        return

    try:
        with Image.open(file_path) as img:
            original_img = img.copy()
            original_img.thumbnail((400, 400))
            tk_img = ImageTk.PhotoImage(original_img)
            image_label.config(image=tk_img, text="")
            image_label.image = tk_img
    except Exception as exc:
        image_label.config(image="", text=f"Could not load image:\n{exc}")
        image_label.image = None
        return

    if reader is None:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"OCR is unavailable.\n{reader_error}")
        annotated_label.config(image="", text="OCR unavailable")
        annotated_label.image = None
        return

    try:
        results = reader.readtext(file_path, detail=1)
        output = "\n".join([item[1] for item in results]) if results else "No text detected."

        annotated_img = Image.open(file_path).copy()
        annotated_img.thumbnail((400, 400))
        draw = ImageDraw.Draw(annotated_img)
        for item in results:
            bbox = item[0]
            points = [(x, y) for x, y in bbox]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            draw.rectangle([min(xs), min(ys), max(xs), max(ys)], outline="red", width=3)

        annotated_tk_img = ImageTk.PhotoImage(annotated_img)
        annotated_label.config(image=annotated_tk_img, text="")
        annotated_label.image = annotated_tk_img
    except Exception as exc:
        output = f"Error during OCR:\n{exc}"
        annotated_label.config(image="", text="Could not generate annotated preview")
        annotated_label.image = None

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, output)


# Main window setup
root = tk.Tk()
root.title("OCR Image Viewer")
root.geometry("650x700")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(0, weight=0)
main_frame.rowconfigure(1, weight=0)
main_frame.rowconfigure(2, weight=1)
main_frame.rowconfigure(3, weight=1)
main_frame.rowconfigure(4, weight=1)

gpu_var = tk.BooleanVar(value=False)
check_gpu = tk.Checkbutton(
    main_frame,
    text="Use GPU",
    variable=gpu_var,
    font=("Arial", 11),
)
check_gpu.grid(row=0, column=0, sticky="w", pady=(0, 10))

btn_select = tk.Button(main_frame, text="Select Image", command=select_and_process_image, font=("Arial", 12))
btn_select.grid(row=1, column=0, pady=(0, 10), sticky="ew")

image_label = tk.Label(main_frame, text="No image selected", bg="#e0e0e0", anchor="center")
image_label.grid(row=2, column=0, sticky="nsew", padx=(0, 0), pady=(0, 5))

annotated_label = tk.Label(main_frame, text="Annotated preview will appear here", bg="#f5f5f5", anchor="center")
annotated_label.grid(row=2, column=0, sticky="nsew", padx=(0, 0), pady=(0, 5))

output_label = tk.Label(main_frame, text="OCR Output", anchor="w", font=("Arial", 11, "bold"))
output_label.grid(row=3, column=0, sticky="ew", pady=(0, 5))

output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=("Arial", 10))
output_text.grid(row=4, column=0, sticky="nsew")

main_frame.rowconfigure(4, weight=1)

root.mainloop()
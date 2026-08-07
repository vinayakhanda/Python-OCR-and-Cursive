import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk

try:
    import easyocr
except ImportError:
    easyocr = None

reader = None
reader_error = ""

if easyocr is not None:
    try:
        reader = easyocr.Reader(["en"], gpu=False)
    except Exception as exc:
        reader_error = str(exc)
        reader = None
else:
    reader_error = "easyocr is not installed."


def select_and_process_image():
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")],
    )

    if not file_path:
        return

    try:
        with Image.open(file_path) as img:
            img.thumbnail((400, 400))
            tk_img = ImageTk.PhotoImage(img)
            image_label.config(image=tk_img, text="")
            image_label.image = tk_img
    except Exception as exc:
        image_label.config(image="", text=f"Could not load image:\n{exc}")
        image_label.image = None
        return

    if reader is None:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"OCR is unavailable.\n{reader_error}")
        return

    try:
        result = reader.readtext(file_path, detail=0)
        output = "\n".join(result) if result else "No text detected."
    except Exception as exc:
        output = f"Error during OCR:\n{exc}"

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, output)


# Main window setup
root = tk.Tk()
root.title("OCR Image Viewer")
root.geometry("650x700")

btn_select = tk.Button(root, text="Select Image", command=select_and_process_image, font=("Arial", 12))
btn_select.pack(pady=15)

image_label = tk.Label(root, text="No image selected", bg="#e0e0e0")
image_label.pack(fill="both", expand=True, padx=20, pady=(0, 10))

output_label = tk.Label(root, text="OCR Output", anchor="w", font=("Arial", 11, "bold"))
output_label.pack(fill="x", padx=20)

output_text = scrolledtext.ScrolledText(root, height=10, wrap=tk.WORD, font=("Arial", 10))
output_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

root.mainloop()
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

from app.core.pdf_engine import PDFEngine
from app.core.exceptions import PDFSuiteException

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class PDFApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("PDF Toolkit Pro")
        self.geometry("920x620")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Internal state trackers
        self.merge_files: list[Path] = []
        self.image_files: list[Path] = []
        self.extract_path = ctk.StringVar()
        self.delete_path = ctk.StringVar()
        self.rotate_path = ctk.StringVar()
        self.text_path = ctk.StringVar()
        self.watermark_path = ctk.StringVar()

        self._setup_sidebar()
        self._setup_views()
        self.show_frame("merge")

    # ---------------- SIDEBAR ----------------

    def _setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        brand_label = ctk.CTkLabel(
            sidebar, text="PDF TOOLKIT", font=ctk.CTkFont(size=20, weight="bold")
        )
        brand_label.pack(padx=20, pady=(20, 15))

        nav_buttons = [
            ("Merge PDFs", "merge"),
            ("Extract Pages", "extract"),
            ("Delete Pages", "delete"),
            ("Rotate Pages", "rotate"),
            ("Extract Text", "text"),
            ("Images → PDF", "img2pdf"),
            ("Watermark", "watermark"),
        ]

        for title, key in nav_buttons:
            btn = ctk.CTkButton(
                sidebar,
                text=title,
                width=170,
                command=lambda k=key: self.show_frame(k),
            )
            btn.pack(padx=15, pady=5)

    def _setup_views(self):
        self.frames = {
            "merge": ctk.CTkFrame(self, corner_radius=10),
            "extract": ctk.CTkFrame(self, corner_radius=10),
            "delete": ctk.CTkFrame(self, corner_radius=10),
            "rotate": ctk.CTkFrame(self, corner_radius=10),
            "text": ctk.CTkFrame(self, corner_radius=10),
            "img2pdf": ctk.CTkFrame(self, corner_radius=10),
            "watermark": ctk.CTkFrame(self, corner_radius=10),
        }

        self._build_merge_view(self.frames["merge"])
        self._build_extract_view(self.frames["extract"])
        self._build_delete_view(self.frames["delete"])
        self._build_rotate_view(self.frames["rotate"])
        self._build_text_view(self.frames["text"])
        self._build_img2pdf_view(self.frames["img2pdf"])
        self._build_watermark_view(self.frames["watermark"])

    def show_frame(self, key: str):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[key].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # ---------------- VIEW BUILDERS ----------------

    def _build_merge_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Merge PDF Documents", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        self.merge_listbox = ctk.CTkTextbox(frame, height=220, width=560, state="disabled")
        self.merge_listbox.pack(pady=10)
        ctk.CTkButton(frame, text="Select Files...", command=self._pick_merge_files).pack(pady=6)
        ctk.CTkButton(frame, text="Merge & Save", fg_color="#2ecc71", hover_color="#27ae60", command=self._run_merge).pack(pady=15)

    def _build_extract_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Extract Pages", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Select Source PDF...", command=lambda: self._pick_single_file(self.extract_path)).pack(pady=6)
        ctk.CTkLabel(frame, textvariable=self.extract_path, wraplength=520, text_color="gray").pack(pady=2)
        ctk.CTkLabel(frame, text="Pages to Extract (1-based, e.g. 1, 3, 5):").pack(pady=(15, 2))
        self.extract_pages_entry = ctk.CTkEntry(frame, width=320, placeholder_text="e.g. 1, 2, 4")
        self.extract_pages_entry.pack(pady=5)
        ctk.CTkButton(frame, text="Extract & Save Copy", fg_color="#2ecc71", hover_color="#27ae60", command=self._run_extract).pack(pady=20)

    def _build_delete_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Delete Pages", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Select Source PDF...", command=lambda: self._pick_single_file(self.delete_path)).pack(pady=6)
        ctk.CTkLabel(frame, textvariable=self.delete_path, wraplength=520, text_color="gray").pack(pady=2)
        ctk.CTkLabel(frame, text="Pages to Delete (1-based, e.g. 2, 4):").pack(pady=(15, 2))
        self.delete_pages_entry = ctk.CTkEntry(frame, width=320, placeholder_text="e.g. 2, 3")
        self.delete_pages_entry.pack(pady=5)
        ctk.CTkButton(frame, text="Delete & Save Copy", fg_color="#e74c3c", hover_color="#c0392b", command=self._run_delete).pack(pady=20)

    def _build_rotate_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Rotate Pages", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Select Source PDF...", command=lambda: self._pick_single_file(self.rotate_path)).pack(pady=6)
        ctk.CTkLabel(frame, textvariable=self.rotate_path, wraplength=520, text_color="gray").pack(pady=2)
        ctk.CTkLabel(frame, text="Rotation Angle (Clockwise):").pack(pady=(10, 2))
        self.rotate_angle_select = ctk.CTkComboBox(frame, values=["90", "180", "270"], width=160)
        self.rotate_angle_select.pack(pady=5)
        ctk.CTkLabel(frame, text="Pages (Leave empty for all pages):").pack(pady=(10, 2))
        self.rotate_pages_entry = ctk.CTkEntry(frame, width=320, placeholder_text="Optional: e.g. 1, 3")
        self.rotate_pages_entry.pack(pady=5)
        ctk.CTkButton(frame, text="Apply Rotation (In-place)", fg_color="#3498db", hover_color="#2980b9", command=self._run_rotate).pack(pady=20)

    def _build_text_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Extract Selectable Text", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Select Source PDF...", command=lambda: self._pick_single_file(self.text_path)).pack(pady=6)
        ctk.CTkLabel(frame, textvariable=self.text_path, wraplength=520, text_color="gray").pack(pady=2)
        self.text_display = ctk.CTkTextbox(frame, height=180, width=560)
        self.text_display.pack(pady=10)
        ctk.CTkButton(frame, text="Extract & View Text", fg_color="#3498db", hover_color="#2980b9", command=self._run_text_extract).pack(pady=5)

    def _build_img2pdf_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Convert Images to PDF", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        self.img_listbox = ctk.CTkTextbox(frame, height=220, width=560, state="disabled")
        self.img_listbox.pack(pady=10)
        ctk.CTkButton(frame, text="Select Images (PNG/JPG)...", command=self._pick_images).pack(pady=6)
        ctk.CTkButton(frame, text="Convert & Save PDF", fg_color="#2ecc71", hover_color="#27ae60", command=self._run_img2pdf).pack(pady=15)

    def _build_watermark_view(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(frame, text="Add Text Watermark", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Select Source PDF...", command=lambda: self._pick_single_file(self.watermark_path)).pack(pady=6)
        ctk.CTkLabel(frame, textvariable=self.watermark_path, wraplength=520, text_color="gray").pack(pady=2)
        ctk.CTkLabel(frame, text="Watermark Text:").pack(pady=(15, 2))
        self.watermark_text_entry = ctk.CTkEntry(frame, width=320, placeholder_text="e.g. CONFIDENTIAL / DRAFT")
        self.watermark_text_entry.pack(pady=5)
        ctk.CTkButton(frame, text="Apply Watermark & Save", fg_color="#2ecc71", hover_color="#27ae60", command=self._run_watermark).pack(pady=20)

    # ---------------- HANDLERS ----------------

    def _pick_merge_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Documents", "*.pdf")])
        if paths:
            self.merge_files = [Path(p) for p in paths]
            self.merge_listbox.configure(state="normal")
            self.merge_listbox.delete("1.0", "end")
            for path in self.merge_files:
                self.merge_listbox.insert("end", f"• {path.name}\n")
            self.merge_listbox.configure(state="disabled")

    def _pick_images(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        if paths:
            self.image_files = [Path(p) for p in paths]
            self.img_listbox.configure(state="normal")
            self.img_listbox.delete("1.0", "end")
            for path in self.image_files:
                self.img_listbox.insert("end", f"• {path.name}\n")
            self.img_listbox.configure(state="disabled")

    def _pick_single_file(self, target_var: ctk.StringVar):
        path = filedialog.askopenfilename(filetypes=[("PDF Documents", "*.pdf")])
        if path:
            target_var.set(path)

    def _parse_pages(self, raw_input: str) -> list[int]:
        if not raw_input.strip():
            return []
        return [int(p.strip()) for p in raw_input.split(",") if p.strip().isdigit()]

    def _run_merge(self):
        if len(self.merge_files) < 2:
            messagebox.showwarning("Input Warning", "Select at least 2 PDF files to merge.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not out_path:
            return
        try:
            PDFEngine.merge_pdfs(self.merge_files, Path(out_path))
            messagebox.showinfo("Success", "PDFs merged successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_extract(self):
        src = self.extract_path.get()
        pages = self._parse_pages(self.extract_pages_entry.get())
        if not src or not pages:
            messagebox.showwarning("Input Warning", "Specify source PDF and page numbers.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not out_path:
            return
        try:
            PDFEngine.extract_pages(Path(src), pages, Path(out_path))
            messagebox.showinfo("Success", f"{len(pages)} page(s) extracted successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_delete(self):
        src = self.delete_path.get()
        pages = self._parse_pages(self.delete_pages_entry.get())
        if not src or not pages:
            messagebox.showwarning("Input Warning", "Select source PDF and pages to delete.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")] )
        if not out_path:
            return
        try:
            PDFEngine.delete_pages(Path(src), pages, Path(out_path))
            messagebox.showinfo("Success", "Pages deleted and saved successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_rotate(self):
        src = self.rotate_path.get()
        if not src:
            messagebox.showwarning("Input Warning", "Select a source PDF.")
            return
        angle = int(self.rotate_angle_select.get())
        raw_pages = self.rotate_pages_entry.get().strip()
        pages = self._parse_pages(raw_pages) if raw_pages else None
        try:
            PDFEngine.rotate_page(Path(src), rotation_degree=angle, pages=pages, output_path=None)
            messagebox.showinfo("Success", f"Document rotated by {angle}° successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_text_extract(self):
        src = self.text_path.get()
        if not src:
            messagebox.showwarning("Input Warning", "Select a source PDF.")
            return
        try:
            text = PDFEngine.extract_text(Path(src))
            self.text_display.delete("1.0", "end")
            self.text_display.insert("1.0", text)
            messagebox.showinfo("Success", "Text extracted successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_img2pdf(self):
        if not self.image_files:
            messagebox.showwarning("Input Warning", "Please select at least 1 image.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not out_path:
            return
        try:
            PDFEngine.images_to_pdf(self.image_files, Path(out_path))
            messagebox.showinfo("Success", "Images converted to PDF successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))

    def _run_watermark(self):
        src = self.watermark_path.get()
        wm_text = self.watermark_text_entry.get().strip()
        if not src or not wm_text:
            messagebox.showwarning("Input Warning", "Provide both a source PDF and watermark text.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not out_path:
            return
        try:
            PDFEngine.add_watermark(Path(src), wm_text, Path(out_path))
            messagebox.showinfo("Success", "Watermark applied and saved successfully!")
        except PDFSuiteException as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = PDFApp()
    app.mainloop()
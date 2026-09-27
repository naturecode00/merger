"""
Relax Waters — Batch Audio Loop & Video Merger
------------------------------------------------
GUI app untuk memproses banyak file audio sekaligus:
1. Loop tiap file audio sampai durasi target
2. Gabung dengan 1 background (gambar atau video) jadi file .mp4
3. Simpan semua hasil ke folder output

Butuh FFmpeg terinstall dan ada di PATH sistem.
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_BG = "#141B34"
PANEL_BG = "#1B2340"
FIELD_BG = "#222B4C"
IVORY = "#F3F1E7"
BLUE = "#6E93C7"
INDIGO = "#4B5FA6"
MUTED = "#8B93B8"

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".bmp")
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")


def resource_path(relative_path):
    """Untuk kompatibilitas kalau nanti di-bundle PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def check_ffmpeg_available():
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


class BatchMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Relax Waters — Batch Audio Loop & Video Merger")
        self.root.geometry("760x620")
        self.root.configure(bg=APP_BG)
        self.root.minsize(680, 560)

        self.audio_files = []
        self.background_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.duration_hours = tk.StringVar(value="3")
        self.preset = tk.StringVar(value="fast")
        self.bitrate = tk.StringVar(value="192k")
        self.is_running = False

        self._build_style()
        self._build_ui()

        if not check_ffmpeg_available():
            self._log(
                "⚠️  FFmpeg tidak ditemukan di PATH. Install dulu dan "
                "pastikan bisa dipanggil dari Command Prompt sebelum lanjut.\n"
            )

    # ---------------- UI SETUP ----------------
    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure(
            "TLabel", background=APP_BG, foreground=IVORY, font=("Segoe UI", 10)
        )
        style.configure(
            "Panel.TLabel", background=PANEL_BG, foreground=IVORY, font=("Segoe UI", 10)
        )
        style.configure(
            "Heading.TLabel",
            background=APP_BG,
            foreground=IVORY,
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "Muted.TLabel", background=PANEL_BG, foreground=MUTED, font=("Segoe UI", 9)
        )
        style.configure(
            "Accent.TButton",
            background=INDIGO,
            foreground=IVORY,
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Accent.TButton", background=[("active", "#5B70BC")])
        style.configure(
            "Secondary.TButton",
            background=FIELD_BG,
            foreground=IVORY,
            font=("Segoe UI", 9),
            padding=6,
        )
        style.map("Secondary.TButton", background=[("active", "#2C376A")])
        style.configure(
            "TEntry", fieldbackground=FIELD_BG, foreground=IVORY, insertcolor=IVORY
        )
        style.configure(
            "TCombobox", fieldbackground=FIELD_BG, foreground=IVORY
        )

    def _build_ui(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=20, pady=(18, 6))
        ttk.Label(header, text="🌧️ Batch Audio Loop & Video Merger", style="Heading.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="Proses banyak file audio sekaligus jadi video panjang siap upload.",
            style="TLabel",
        ).pack(anchor="w", pady=(2, 0))

        body = ttk.Frame(self.root, style="TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # ---- Panel: Audio files ----
        panel1 = tk.Frame(body, bg=PANEL_BG, padx=14, pady=12)
        panel1.pack(fill="x", pady=(0, 10))
        ttk.Label(panel1, text="1. File audio (bisa pilih banyak sekaligus)", style="Panel.TLabel").pack(
            anchor="w"
        )
        list_frame = tk.Frame(panel1, bg=PANEL_BG)
        list_frame.pack(fill="x", pady=6)
        self.audio_listbox = tk.Listbox(
            list_frame,
            height=5,
            bg=FIELD_BG,
            fg=IVORY,
            selectbackground=INDIGO,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#2C376A",
        )
        self.audio_listbox.pack(side="left", fill="both", expand=True)
        btns = tk.Frame(list_frame, bg=PANEL_BG)
        btns.pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Tambah File", style="Secondary.TButton", command=self.add_audio_files).pack(
            fill="x", pady=2
        )
        ttk.Button(btns, text="Hapus Terpilih", style="Secondary.TButton", command=self.remove_selected).pack(
            fill="x", pady=2
        )
        ttk.Button(btns, text="Kosongkan", style="Secondary.TButton", command=self.clear_audio).pack(
            fill="x", pady=2
        )

        # ---- Panel: Background ----
        panel2 = tk.Frame(body, bg=PANEL_BG, padx=14, pady=12)
        panel2.pack(fill="x", pady=(0, 10))
        ttk.Label(panel2, text="2. Background (gambar atau video pendek)", style="Panel.TLabel").pack(
            anchor="w"
        )
        row = tk.Frame(panel2, bg=PANEL_BG)
        row.pack(fill="x", pady=6)
        entry_bg = tk.Entry(
            row, textvariable=self.background_path, bg=FIELD_BG, fg=IVORY, insertbackground=IVORY,
            borderwidth=0, highlightthickness=1, highlightbackground="#2C376A"
        )
        entry_bg.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(row, text="Pilih File", style="Secondary.TButton", command=self.pick_background).pack(
            side="left", padx=(8, 0)
        )

        # ---- Panel: Settings ----
        panel3 = tk.Frame(body, bg=PANEL_BG, padx=14, pady=12)
        panel3.pack(fill="x", pady=(0, 10))
        ttk.Label(panel3, text="3. Pengaturan", style="Panel.TLabel").pack(anchor="w")

        settings_row = tk.Frame(panel3, bg=PANEL_BG)
        settings_row.pack(fill="x", pady=6)

        col1 = tk.Frame(settings_row, bg=PANEL_BG)
        col1.pack(side="left", padx=(0, 16))
        ttk.Label(col1, text="Durasi target (jam)", style="Muted.TLabel").pack(anchor="w")
        tk.Entry(
            col1, textvariable=self.duration_hours, width=8, bg=FIELD_BG, fg=IVORY,
            insertbackground=IVORY, borderwidth=0, highlightthickness=1, highlightbackground="#2C376A"
        ).pack(pady=(2, 0), ipady=4)

        col2 = tk.Frame(settings_row, bg=PANEL_BG)
        col2.pack(side="left", padx=(0, 16))
        ttk.Label(col2, text="Kecepatan render", style="Muted.TLabel").pack(anchor="w")
        ttk.Combobox(
            col2, textvariable=self.preset, values=["ultrafast", "fast", "medium"],
            width=10, state="readonly"
        ).pack(pady=(2, 0))

        col3 = tk.Frame(settings_row, bg=PANEL_BG)
        col3.pack(side="left")
        ttk.Label(col3, text="Bitrate audio", style="Muted.TLabel").pack(anchor="w")
        ttk.Combobox(
            col3, textvariable=self.bitrate, values=["128k", "192k", "256k", "320k"],
            width=10, state="readonly"
        ).pack(pady=(2, 0))

        # ---- Panel: Output ----
        panel4 = tk.Frame(body, bg=PANEL_BG, padx=14, pady=12)
        panel4.pack(fill="x", pady=(0, 10))
        ttk.Label(panel4, text="4. Folder output", style="Panel.TLabel").pack(anchor="w")
        row2 = tk.Frame(panel4, bg=PANEL_BG)
        row2.pack(fill="x", pady=6)
        tk.Entry(
            row2, textvariable=self.output_folder, bg=FIELD_BG, fg=IVORY, insertbackground=IVORY,
            borderwidth=0, highlightthickness=1, highlightbackground="#2C376A"
        ).pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(row2, text="Pilih Folder", style="Secondary.TButton", command=self.pick_output_folder).pack(
            side="left", padx=(8, 0)
        )

        # ---- Run button ----
        run_row = tk.Frame(body, bg=APP_BG)
        run_row.pack(fill="x", pady=(4, 8))
        self.run_btn = ttk.Button(
            run_row, text="▶  Mulai Proses Semua", style="Accent.TButton", command=self.start_batch
        )
        self.run_btn.pack(fill="x", ipady=4)

        # ---- Log ----
        log_frame = tk.Frame(body, bg=PANEL_BG, padx=10, pady=8)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame, bg="#0E1226", fg=IVORY, insertbackground=IVORY,
            borderwidth=0, font=("Consolas", 9), wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    # ---------------- ACTIONS ----------------
    def add_audio_files(self):
        files = filedialog.askopenfilenames(
            title="Pilih file audio",
            filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a"), ("Semua file", "*.*")],
        )
        for f in files:
            if f not in self.audio_files:
                self.audio_files.append(f)
                self.audio_listbox.insert("end", os.path.basename(f))

    def remove_selected(self):
        sel = list(self.audio_listbox.curselection())
        sel.reverse()
        for i in sel:
            self.audio_listbox.delete(i)
            del self.audio_files[i]

    def clear_audio(self):
        self.audio_listbox.delete(0, "end")
        self.audio_files = []

    def pick_background(self):
        f = filedialog.askopenfilename(
            title="Pilih background",
            filetypes=[
                ("Gambar atau video", "*.jpg *.jpeg *.png *.bmp *.mp4 *.mov *.mkv *.webm"),
                ("Semua file", "*.*"),
            ],
        )
        if f:
            self.background_path.set(f)

    def pick_output_folder(self):
        d = filedialog.askdirectory(title="Pilih folder output")
        if d:
            self.output_folder.set(d)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def start_batch(self):
        if self.is_running:
            return
        if not self.audio_files:
            messagebox.showwarning("Belum lengkap", "Tambahkan minimal 1 file audio dulu.")
            return
        if not self.background_path.get():
            messagebox.showwarning("Belum lengkap", "Pilih background (gambar/video) dulu.")
            return
        if not self.output_folder.get():
            messagebox.showwarning("Belum lengkap", "Pilih folder output dulu.")
            return
        try:
            hours = float(self.duration_hours.get())
            if hours <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Durasi tidak valid", "Isi durasi target dengan angka lebih dari 0.")
            return

        self.is_running = True
        self.run_btn.configure(state="disabled")
        thread = threading.Thread(target=self._run_batch_thread, args=(hours,), daemon=True)
        thread.start()

    def _run_batch_thread(self, hours):
        seconds = int(hours * 3600)
        bg = self.background_path.get()
        out_dir = self.output_folder.get()
        is_bg_video = bg.lower().endswith(VIDEO_EXT)
        total = len(self.audio_files)

        self._log(f"=== Mulai proses {total} file, target durasi {hours} jam ===\n")

        success, failed = 0, 0
        for idx, audio_path in enumerate(self.audio_files, start=1):
            name = os.path.splitext(os.path.basename(audio_path))[0]
            safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
            temp_audio = os.path.join(out_dir, f"__temp_{safe_name}.mp3")
            final_output = os.path.join(out_dir, f"{safe_name}.mp4")

            self._log(f"[{idx}/{total}] Memproses: {os.path.basename(audio_path)}")

            try:
                # Step 1: loop audio ke durasi target
                self._log("   → Loop audio ke durasi target...")
                cmd_loop = [
                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", audio_path,
                    "-t", str(seconds), "-c:a", "libmp3lame", "-b:a", self.bitrate.get(),
                    temp_audio,
                ]
                subprocess.run(cmd_loop, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Step 2: gabung dengan background
                self._log("   → Gabung dengan background jadi video...")
                if is_bg_video:
                    cmd_merge = [
                        "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg, "-i", temp_audio,
                        "-c:v", "libx264", "-preset", self.preset.get(), "-c:a", "aac",
                        "-b:a", self.bitrate.get(), "-map", "0:v:0", "-map", "1:a:0",
                        "-shortest", final_output,
                    ]
                else:
                    cmd_merge = [
                        "ffmpeg", "-y", "-loop", "1", "-i", bg, "-i", temp_audio,
                        "-c:v", "libx264", "-preset", self.preset.get(), "-tune", "stillimage",
                        "-c:a", "aac", "-b:a", self.bitrate.get(), "-pix_fmt", "yuv420p",
                        "-shortest", final_output,
                    ]
                subprocess.run(cmd_merge, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                os.remove(temp_audio)
                self._log(f"   ✅ Selesai: {os.path.basename(final_output)}\n")
                success += 1

            except subprocess.CalledProcessError:
                self._log(f"   ❌ Gagal memproses file ini (cek apakah file audio/background valid)\n")
                failed += 1
            except Exception as e:
                self._log(f"   ❌ Error: {e}\n")
                failed += 1

        self._log(f"=== Selesai semua. Berhasil: {success}, Gagal: {failed} ===")
        self.is_running = False
        self.run_btn.configure(state="normal")
        messagebox.showinfo("Selesai", f"Proses selesai.\nBerhasil: {success}\nGagal: {failed}")


def main():
    root = tk.Tk()
    app = BatchMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

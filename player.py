import os
import json
import random
import tkinter as tk
from tkinter import filedialog
import pygame

CONFIG_FILE = os.path.expanduser("~/Documents/Projects/mp3-player-app/config.json")


class SimpleMP3Player:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Reproductor MP3")
        self.root.geometry("520x360")
        self.root.resizable(False, False)

        FONT_SYMBOLS = ("DejaVu Sans", 10)

        pygame.mixer.init()

        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False

        self.is_shuffle = False
        self.shuffle_order = []

        self.lbl_song = tk.Label(
            root,
            text="Sin carpeta seleccionada",
            font=("DejaVu Sans", 9),
            wraplength=420,
            fg="gray",
        )
        self.lbl_song.pack(pady=5)

        frame_search = tk.Frame(root)
        frame_search.pack(pady=5, fill=tk.X, padx=15)

        tk.Label(frame_search, text="Buscar:", font=("Dejavu Sans", 9)).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_songs)

        self.entry_search = tk.Entry(
            frame_search, textvariable=self.search_var, font=("DejaVu Sans", 10)
        )
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_clear_search = tk.Button(
            frame_search,
            text="x",
            font=("DejaVu Sans", 8, "bold"),
            command=self.clear_search,
            relief=tk.FLAT,
            fg="red",
        )
        self.btn_clear_search.pack(side=tk.LEFT, padx=(5, 0))

        frame_list = tk.Frame(root)
        frame_list.pack(pady=5, fill=tk.BOTH, expand=True, padx=15)

        self.scrollbar = tk.Scrollbar(frame_list)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            frame_list,
            yscrollcommand=self.scrollbar.set,
            selectmode=tk.SINGLE,
            height=8,
            font=("DejaVu Sans", 9),
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", self.on_select_song)

        btn_folder = tk.Button(
            root,
            text="[Carpeta] Seleccionar Carpeta de Música",
            font=FONT_SYMBOLS,
            command=self.select_folder,
        )
        btn_folder.pack(pady=5)

        frame_controls = tk.Frame(root)
        frame_controls.pack(pady=10)

        tk.Button(
            frame_controls,
            text="<< Anterior",
            font=FONT_SYMBOLS,
            command=self.prev_song,
            width=9,
        ).pack(side=tk.LEFT, padx=3)
        self.btn_play = tk.Button(
            frame_controls,
            text="Play / Pause",
            font=FONT_SYMBOLS,
            command=self.toggle_play,
            width=9,
        )
        self.btn_play.pack(side=tk.LEFT, padx=3)
        tk.Button(
            frame_controls,
            text="Stop []",
            font=FONT_SYMBOLS,
            command=self.stop_song,
            width=9,
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            frame_controls,
            text="Siguiente >>",
            font=FONT_SYMBOLS,
            command=self.next_song,
            width=9,
        ).pack(side=tk.LEFT, padx=3)

        self.btn_shuffle = tk.Button(
            frame_controls,
            text="Shuffle: OFF",
            font=FONT_SYMBOLS,
            command=self.toggle_shuffle,
            width=12,
            bg="lightgray",
        )
        self.btn_shuffle.pack(side=tk.LEFT, padx=3)

        self.load_config()

        self.check_music_end()

    def select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if folder:
            self.load_songs_from_folder(folder)
            self.save_config(folder)

    def load_songs_from_folder(self, folder_path) -> None:
        if not os.path.exists(folder_path):
            return

        self.playlist = []
        self.listbox.delete(0, tk.END)

        for file in sorted(os.listdir(folder_path)):
            if file.lower().endswith(".mp3"):
                full_path = os.path.join(folder_path, file)
                self.playlist.append(full_path)
                self.listbox.insert(tk.END, file)

        if self.playlist:
            self.current_index = 0
            self.lbl_song.config(
                text=f"Carpeta: {os.path.basename(folder_path)} ({len(self.playlist)} canciones)",
                fg="black",
            )
        else:
            self.lbl_song.config(
                text="No se encontraron archivos MP3 en la carpeta.", fg="red"
            )

    def play_song(self) -> None:
        if not self.playlist:
            return

        song_path = self.playlist[self.current_index]
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()

        self.is_playing = True
        self.is_paused = False

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.current_index)
        self.listbox.activate(self.current_index)

        self.lbl_song.config(text=f"▶ {os.path.basename(song_path)}", fg="green")

    def toggle_play(self) -> None:
        if not self.playlist:
            return

        if not self.is_playing:
            self.play_song()
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.lbl_song.config(fg="green")
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.lbl_song.config(fg="orange")

    def stop_song(self) -> None:
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.lbl_song.config(text="Detenido", fg="gray")

    def toggle_shuffle(self) -> None:
        if not self.playlist:
            return

        self.is_shuffle = not self.is_shuffle

        if self.is_shuffle:
            self.btn_shuffle.config(text="Shuffle: ON")
            self.shuffle_order = list(range(len(self.playlist)))
            random.shuffle(self.shuffle_order)

            if self.current_index in self.shuffle_order:
                self.shuffle_order.remove(self.current_index)
                self.shuffle_order.insert(0, self.current_index)
        else:
            self.btn_shuffle.config(text="Shuffle: OFF")

    def next_song(self) -> None:
        if not self.playlist:
            return

        if self.is_shuffle and self.shuffle_order:
            try:
                current_shuffle_pos = self.shuffle_order.index(self.current_index)
                next_shuffle_pos = (current_shuffle_pos + 1) % len(self.shuffle_order)
                self.current_index = self.shuffle_order[next_shuffle_pos]
            except ValueError:
                self.current_index = random.choice(self.shuffle_order)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)

        self.play_song()

    def prev_song(self) -> None:
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_song()

    def on_select_song(self, event) -> None:
        selection = self.listbox.curselection()
        if selection:
            selected_file_name = self.listbox.get(selection[0])
            for index, song_path in enumerate(self.playlist):
                if os.path.basename(song_path) == selected_file_name:
                    self.current_index = index
                    self.play_song()
                    break

    def check_music_end(self) -> None:
        if self.is_playing and not self.is_paused:
            if not pygame.mixer.music.get_busy():
                self.next_song()
        self.root.after(1000, self.check_music_end)

    def save_config(self, folder_path) -> None:
        try:
            with open(CONFIG_FILE, "r") as f:
                json.dump({"last_folder": folder_path}, f)
        except Exception:
            pass

    def load_config(self) -> None:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    folder = data.get("last_folder")
                    if folder and os.path.exists(folder):
                        self.load_songs_from_folder(folder)
            except Exception:
                pass

    def filter_songs(self, *args) -> None:
        search_text = self.search_var.get().lower()

        self.listbox.delete(0, tk.END)

        for song_path in self.playlist:
            file_name = os.path.basename(song_path)

            if search_text in file_name.lower():
                self.listbox.insert(tk.END, file_name)

    def clear_search(self) -> None:
        self.search_var.set("")
        self.entry_search.focus()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleMP3Player(root)
    root.mainloop()

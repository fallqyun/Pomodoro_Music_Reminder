import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image, ImageDraw
import io, requests, threading, json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pages import pomodoro_page
from pages import library_page
from pages import home_page  
from pages import search_page
import tkinter as tk

# ---------------- Load config ----------------
import os
from dotenv import load_dotenv

# Muat .env
load_dotenv()

# Muat config.json
with open("config.json", "r") as f:
    config = json.load(f)

# Ambil kredensial dari .env
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

if not client_id or not client_secret or not redirect_uri:
    raise Exception("❌ .env tidak lengkap! Pastikan SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, dan SPOTIFY_REDIRECT_URI ada.")

# ---------------- Spotify auth ----------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=" ".join(config["spotify"]["scopes"]),
    cache_path=".spotify_cache.json",
    show_dialog=True
))

# ---------------- CustomTkinter Settings ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ---------------- Root ----------------
root = ctk.CTk()
root.title("Pomodoro Spotify App")
root.geometry("1800x1000")
root.state("zoomed")

# Batasi ukuran minimal
root.minsize(1200, 700)

# ---------------- Sidebar ----------------
sidebar = ctk.CTkFrame(root, width=200, fg_color="#121212")
sidebar.pack(side="left", fill="y", padx=5, pady=5)

# ---------------- Content ----------------
content = ctk.CTkFrame(root, fg_color=config["theme"]["bg"])
content.pack(side="top", fill="both", expand=True, padx=5, pady=5)

# ---------------- Footer / Mini Player ----------------
footer = ctk.CTkFrame(root, height=120)
footer.pack(side="bottom", fill="x")
footer.pack_propagate(False)

# ---- Player Frame ----
player_frame = ctk.CTkFrame(footer, fg_color=footer.cget("fg_color"))
player_frame.pack(fill="both", expand=True, padx=5, pady=5)

# ---- Album Art ----
album_size = 100
album_label = ctk.CTkLabel(player_frame, text="")
album_label.pack(side="left", padx=10, pady=10)
album_label.current_img = None
album_label.original_img = None  # Simpan versi PIL

# ---- Middle Frame: Buttons + Track Info + Progress ----
middle_frame = ctk.CTkFrame(player_frame, fg_color=player_frame.cget("fg_color"))
middle_frame.pack(side="left", expand=True, fill="both")

# Buttons Frame
btn_frame = ctk.CTkFrame(middle_frame, fg_color=middle_frame.cget("fg_color"))
btn_frame.pack(pady=10)

shuffle_btn = ctk.CTkButton(btn_frame, text="🔀", width=30, text_color="white")
shuffle_btn.pack(side="left", padx=5)
prev_btn = ctk.CTkButton(btn_frame, text="⏮", width=30, text_color="white")
prev_btn.pack(side="left", padx=5)
play_pause_btn = ctk.CTkButton(btn_frame, text="▶", width=30, text_color="white")
play_pause_btn.pack(side="left", padx=5)
next_btn = ctk.CTkButton(btn_frame, text="⏭", width=30, text_color="white")
next_btn.pack(side="left", padx=5)
repeat_btn = ctk.CTkButton(btn_frame, text="🔁", width=30, text_color="white")
repeat_btn.pack(side="left", padx=5)

# Track info
track_var = ctk.StringVar(value="Tidak ada lagu yang diputar")
track_label = ctk.CTkLabel(middle_frame, textvariable=track_var, anchor="center")
track_label.pack(pady=(5,2), padx=(10, 0), fill="x")

# Progress bar + time labels
time_frame = ctk.CTkFrame(middle_frame, fg_color=middle_frame.cget("fg_color"))
time_frame.pack(fill="x", padx=10, pady=(5, 10))
current_time_var = ctk.StringVar(value="0:00")
duration_var = ctk.StringVar(value="0:00")
ctk.CTkLabel(time_frame, textvariable=current_time_var, width=40).pack(side="left")
progress_var = ctk.DoubleVar(value=0)
progress_bar = ctk.CTkSlider(time_frame, from_=0, to=100, variable=progress_var, width=200)
progress_bar.pack(side="left", fill="x", expand=True, padx=5)
ctk.CTkLabel(time_frame, textvariable=duration_var, width=40).pack(side="right")

# Spacer kanan
spacer_frame = ctk.CTkFrame(footer, width=100, fg_color=footer.cget("fg_color"))
spacer_frame.pack(side="right", fill="y")

# ---------------- Tooltip Class ----------------
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = ctk.CTkToplevel(self.widget)
        tw.overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, fg_color="gray20", text_color="white", corner_radius=5)
        label.pack()
    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ---------------- Spotify Functions ----------------
def fetch_album_image(url, size=album_size):
    if not url:
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "image" in content_type and len(response.content) > 0:
                pil_img = Image.open(io.BytesIO(response.content)).resize((size, size))
                ctk_img = CTkImage(pil_img, size=(size, size))
                album_label.current_img = ctk_img
                album_label.original_img = pil_img
                return ctk_img
    except Exception as e:
        print(f"❌ Gagal muat gambar: {e}")
    return None

def animate_album_change(new_img):
    if new_img:
        album_label.configure(image=new_img)

def ms_to_minsec(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02}"

def update_track_info_animated():
    last_track_id = None
    while True:
        try:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                artists = ', '.join([a['name'] for a in track['artists']])
                track_var.set(f"{track['name']} - {artists}")
                duration_var.set(ms_to_minsec(track['duration_ms']))
                img_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                if img_url and last_track_id != track['id']:
                    last_track_id = track['id']
                    album_img = fetch_album_image(img_url)
                    if album_img:
                        animate_album_change(album_img)
            else:
                track_var.set("Tidak ada lagu yang diputar")
                album_label.configure(image="")
                album_label.current_img = None
                album_label.original_img = None
                current_time_var.set("0:00")
                duration_var.set("0:00")
        except Exception as e:
            print("Spotify error:", e)
            track_var.set("Koneksi bermasalah")
        threading.Event().wait(1)

def toggle_play_pause():
    try:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            sp.pause_playback()
        else:
            sp.start_playback()
    except:
        pass

def seek_track(value):
    try:
        playback = sp.current_playback()
        if playback and playback.get('item'):
            duration = playback['item']['duration_ms']
            sp.seek_track(int(duration * value / 100))
    except:
        pass

progress_bar.configure(command=seek_track)

def update_play_pause_icon():
    while True:
        try:
            playback = sp.current_playback()
            if playback and playback.get('is_playing'):
                play_pause_btn.configure(text="⏸")
            else:
                play_pause_btn.configure(text="▶")
        except:
            play_pause_btn.configure(text="▶")
        threading.Event().wait(0.5)

def smooth_progress_update():
    while True:
        try:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                current = playback['progress_ms']
                duration = playback['item']['duration_ms']
                current_time_var.set(ms_to_minsec(current))
                if duration > 0:
                    progress_var.set((current / duration) * 100)
            else:
                progress_var.set(0)
        except:
            progress_var.set(0)
        threading.Event().wait(0.5)

def add_smooth_hover(button, hover_color="#1DB954"):
    normal_color = button.cget("fg_color")
    def on_enter(e): button.configure(fg_color=hover_color)
    def on_leave(e): button.configure(fg_color=normal_color)
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

def toggle_shuffle():
    try:
        playback = sp.current_playback()
        if playback:
            sp.shuffle(not playback['shuffle_state'])
    except:
        pass

def toggle_repeat():
    try:
        playback = sp.current_playback()
        if playback:
            state = playback['repeat_state']
            new_state = 'context' if state == 'off' else 'off'
            sp.repeat(new_state)
    except:
        pass

# Daftar tombol
player_buttons = [
    (shuffle_btn, "Shuffle", toggle_shuffle),
    (prev_btn, "Previous", lambda: sp.previous_track()),
    (play_pause_btn, "Play/Pause", toggle_play_pause),
    (next_btn, "Next", lambda: sp.next_track()),
    (repeat_btn, "Repeat", toggle_repeat)
]

for btn, tooltip, cmd in player_buttons:
    add_smooth_hover(btn)
    Tooltip(btn, tooltip)
    btn.configure(command=cmd)

def update_active_buttons():
    while True:
        try:
            playback = sp.current_playback()
            if playback:
                highlight_active(shuffle_btn, playback['shuffle_state'])
                highlight_active(repeat_btn, playback['repeat_state'] != 'off')
        except:
            highlight_active(shuffle_btn, False)
            highlight_active(repeat_btn, False)
        threading.Event().wait(1)

def highlight_active(button, is_active):
    if is_active:
        button.configure(fg_color="#1DB954")
    else:
        button.configure(fg_color=button.master.cget("fg_color"))

# ---------------- Pages ----------------
pages = ["Home", "Library", "Pomodoro", "Search"]
frames = {}

def show_frame(page_name):
    for frame in frames.values():
        frame.pack_forget()
    if page_name == "Pomodoro":
        if "Pomodoro" not in frames:
            frames["Pomodoro"] = pomodoro_page.PomodoroPage(content, config, sp)
        frames["Pomodoro"].pack(fill="both", expand=True)
    elif page_name == "Library":
        if "Library" not in frames:
            frames["Library"] = library_page.LibraryPage(content, config, sp)
        frames["Library"].pack(fill="both", expand=True)
    elif page_name == "Home":
        if "Home" not in frames:
            frames["Home"] = home_page.HomePage(content, config, sp)
        frames["Home"].pack(fill="both", expand=True)
    elif page_name == "Search":
        if "Search" not in frames:
            from pages import search_page
            frames["Search"] = search_page.SearchPage(content, config, sp)
        frames["Search"].pack(fill="both", expand=True)
    else:
        if page_name not in frames:
            frame = ctk.CTkFrame(content, fg_color="transparent")
            ctk.CTkLabel(frame, text=f"{page_name} page", font=("Helvetica", 24)).pack(expand=True)
            frames[page_name] = frame
        frames[page_name].pack(fill="both", expand=True)

# Tambahkan tombol sidebar
for p in pages:
    ctk.CTkButton(sidebar, text=p, command=lambda p=p: show_frame(p)).pack(fill="x", pady=10)

# Tampilkan halaman default
show_frame("Home")

# ---------------- Resize Handling ----------------
def on_resize(event):
    global album_size
    new_size = max(20, min(100, player_frame.winfo_height() - 20))
    if new_size != album_size:
        album_size = new_size
        if album_label.original_img:
            resized = album_label.original_img.resize((album_size, album_size))
            ctk_img = CTkImage(resized, size=(album_size, album_size))
            album_label.configure(image=ctk_img)
            album_label.current_img = ctk_img

root.bind("<Configure>", on_resize)

# ---------------- Start Spotify threads ----------------
threading.Thread(target=update_track_info_animated, daemon=True).start()
threading.Thread(target=update_play_pause_icon, daemon=True).start()
threading.Thread(target=smooth_progress_update, daemon=True).start()
threading.Thread(target=update_active_buttons, daemon=True).start()

# Cek koneksi Spotify
def check_connection():
    try:
        me = sp.current_user()
        print(f"✅ Login berhasil: {me['display_name']}")
    except Exception as e:
        print(f"❌ Login gagal: {e}")

check_connection()

# ---------------- Start GUI ----------------
root.mainloop()
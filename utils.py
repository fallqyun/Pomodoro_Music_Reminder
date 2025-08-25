# utils.py
import tkinter as tk
import random

def create_particle_animation(parent, width=1000, height=600):
    """Buat canvas dengan animasi partikel"""
    # Frame container
    canvas_frame = tk.Frame(parent, bg="#121212")
    canvas_frame.pack(fill="both", expand=True)

    # Canvas untuk partikel
    canvas = tk.Canvas(
        canvas_frame,
        width=width,
        height=height,
        bg="#121212",
        highlightthickness=0
    )
    canvas.pack(fill="both", expand=True)

    # Buat partikel
    particles = []
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 3)
        color = "#1DB954" if random.random() < 0.5 else "#BB86FC"
        particle = canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")
        particles.append((particle, x, y, size))

    def animate():
        for i, (particle, x, y, size) in enumerate(particles):
            new_x = (x + 0.2) % width
            new_y = (y + 0.1) % height
            canvas.coords(particle, new_x, new_y, new_x + size, new_y + size)
            particles[i] = (particle, new_x, new_y, size)
        canvas.after(50, animate)

    animate()
    return canvas_frame, canvas
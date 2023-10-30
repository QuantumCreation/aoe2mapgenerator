import tkinter as tk

n = 10  # size of the grid

def on_click(event):
    # change the color of the clicked square to red
    event.widget.config(bg='red')

root = tk.Tk()

# create the grid
for i in range(n):
    for j in range(n):
        square = tk.Frame(root, width=30, height=30, bg='white')
        square.grid(row=i, column=j)
        square.bind('<Button-1>', on_click)

root.mainloop()

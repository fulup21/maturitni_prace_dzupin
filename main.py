from dixit_game import DixitGame, Player
import tkinter as tk

root = tk.Tk()
p1 = Player(name="Petr",nature="učitelka mateřské školky",temperature=1)
p2 = Player(name="Jana",nature="hloupý Honza",temperature=0.9)
p3 = Player(name="Josef",nature="milovník fyziky", temperature=0.8)
p4 = Player(name="Pavel",nature="farmář, který neumí číst",temperature=0.7)
game = DixitGame([p1,p2,p3,p4], root, debug=True)
root.mainloop()
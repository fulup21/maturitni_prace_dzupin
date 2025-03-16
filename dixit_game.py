from random import shuffle, choice
import os
from abstracts import AbstractCardManager, AbstractPlayer, Card
from import_images import process_images_to_json
from sk import mykey
import openai
import json
import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import logging
import threading
import base64
import hashlib

openai.api_key = mykey  # OpenAI API key

logging.basicConfig(filename='dixit.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w', encoding='utf-8')  # 'w' write mode or 'a' append mode
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("dixit")


class CardManager(AbstractCardManager):
    """An object, which keeps track of all the cards;
    by default loads all images and makes Card instances out of them
    """

    def __init__(self, json_file: str, input_directory: str) -> None:
        self.dict_of_cards: dict[int, Card] = {}
        self.json_file = json_file
        self.input_directory = input_directory
        self.load_cards()

    def load_cards(self) -> None:
        """Loads all the cards from the json file into dict"""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data:list = json.load(f)
            # Validate contents
            if not isinstance(data, list) or not all(
                    'key' in item and 'path' in item and 'checksum' in item and 'encoded_picture' in item for item in
                    data):
                raise ValueError("obsah JSONu je chybný")

            # Check if the number of items in the JSON file matches the number of files in the directory
            num_files_in_directory = len([name for name in os.listdir(self.input_directory) if os.path.isfile(os.path.join(self.input_directory, name))])
            if len(data) != num_files_in_directory:
                raise ValueError(f"Počet obrázků nesedí. V JSONu ({len(data)}) a ve složce ({num_files_in_directory}).")

            # Verify checksums and file existence
            for item in data:
                if not os.path.exists(item['path']):
                    raise FileNotFoundError(f"Soubor '{item['path']}' neexistuje!")

                with open(item['path'], "rb") as _f:
                    b64_image: bytes = base64.b64encode(_f.read())
                    calculated_checksum = hashlib.md5(b64_image).hexdigest()

                if calculated_checksum != item['checksum']:
                    raise ValueError(f"Checksum verifikace selhala u karty s klíčem {item['key']}")

            self.dict_of_cards = {item['key']: Card(**item) for item in data}
            log.info(f"Karty byly úspěšně načteny '{self.json_file}'.")

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            log.info(f"Chyba se souborem '{self.json_file}': {e}. Regeneruji...")
            process_images_to_json(self.input_directory, self.json_file)
            self.load_cards()  # Retry loading after regeneration

    def find_card(self, key: int) -> Card:
        """find a card by key"""
        return self.dict_of_cards[key]



class Player(AbstractPlayer):
    """AI powered player"""

    def __init__(self, name: str, nature: str = "jsi hráč hry dixit", temperature: float = 0) -> None:
        """set how the player will behave"""
        self.nature = nature
        self.temperature = temperature
        self.name = name
        self.cards_on_hand: list[Card] = []
        self.score = 0

    def take_card(self, card: Card) -> None:
        self.cards_on_hand.append(card)

    def make_description(self, card: Card) -> str:
        prompt = """Na základě zadaného obrázku vytvoř originální a abstraktní pojem, který vystihuje jeho atmosféru nebo koncept. 
        Vyhni se přímému popisu věcí na obrázku. 
        Například pro obrázek králíka ve skafandru by správný pojem mohl být "dobrodružství mimozemského života",
        nikoliv "zvířecí astronaut".
        Pojem nesmí být delší než 30 znaků a musí být originální. 
        Vypiš mi pouze tento pojem ve formátu: 'pojem'.
        """
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f" jsi hráč hry Dixit, který odpovídá na dotazy v roli {self.nature}, tvoje role by se mela odrazit v tom jak odpovidáš na dotazy"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{card.encoded_picture}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_completion_tokens=75,
            n=1,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def choose_card(self, description: str, laid_out_cards: list[Card]) -> Card:
        """look at all cards 'on the table' and compare them with the description"""

        prompt = f"Na základě zadaných obrázků vyber ten, který nejlépe sedí zadanému popisu:{description}. Napiš mi pouze číslo karty ve formatu:1"
        built_message:list[dict[str,str|dict[str,str]]] = [{
            "type": "text",
            "text": prompt,
        }]
        for i in range(len(laid_out_cards)):
            g = {"type": "image_url",
                 "image_url": {
                     "url": f"data:image/png;base64,{laid_out_cards[i].encoded_picture}",
                     "detail": "low"}}
            built_message.append(g)

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f" jsi hráč hry Dixit, který odpovídá na dotazy v roli {self.nature}, tvoje role by se mela odrazit v tom jak se rozhoduješ"
                },
                {
                    "role": "user",
                    "content": built_message,
                }
            ],
            max_tokens=300,
            n=1,
            temperature=self.temperature
        )
        return laid_out_cards[int(response.choices[0].message.content) - 1]

    def score_add(self, number: int) -> None:
        self.score += number



class DixitGame:
    """Simulates a game of Dixit; set debug=True to simulate without any API calls

    """

    def     __init__(self, players: list[Player], root_window: tk.Tk, debug: bool = False) -> None:
        log.info("Začátek aplikace")
        ################################ GAME SETUP ################################
        # Initialize game settings
        self.debug = debug
        self.number_of_players = 4
        self.players: list[Player] = players
        self.cards_in_deck: list[Card] = []
        self.discard_pile: list[Card] = []
        self.cards_on_table: list[tuple[Card, Player]] = []
        self.number_of_cards_per_player: int = 6
        self.round_number: int = 1
        self.index_storyteller: int = 0
        self.manager = CardManager("images.json", "card_images")
        self.shuffle_cards()
        self.hand_out_cards()

        ################################ UI SETUP ###################################
        # Initialize UI components
        self.backgrounds: list[str] = ['dodger blue', 'IndianRed1', 'slate blue', 'PaleGreen1']
        self.card_images: list[ImageTk] = []


        # Set up the main Tkinter window
        self.root = root_window
        self.root.geometry("1920x1200")
        self.root.title("Dixit Game")
        self.root.state("zoomed")

        self.canvas = Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.update()
        self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2 - 200,
                                text="Simulace hry Dixit s openai", font=("Arial", 60), anchor=tk.CENTER)
        self.canvas.create_text(self.canvas.winfo_width() // 2, (self.canvas.winfo_height() // 2) - 130,
                                text="Pro spuštění zmáčkněte tlačítko 'Začít hru', pro zobrazení logu zmáčkněte tlačítko 'Log'",
                                font=("Arial", 18), anchor=tk.CENTER)

        # Create a bottom bar
        self.bottom_bar = tk.Frame(self.root, height=50, bg='lightgrey')
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Big button to start the game, gets deleted after the first turn
        self.start_game_button = tk.Button(self.canvas, text='Začít hru', font=("Arial", 60), command=self.play_turn)
        self.start_game_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

        self.play_button = tk.Button(self.bottom_bar, text='Zahraj další tah', command=self.play_turn)

        self.log_button = tk.Button(self.bottom_bar, text="Log", command=self.show_log)
        self.log_button.pack(side=tk.LEFT, padx=2, pady=1)

        # Log player creation
        for player in self.players:
            log.info(f'Vytvořen hráč jménem {player.name} s povahou {player.nature} a temperature {player.temperature}')

    def turn(self, storyteller_idx: int) -> None:
        """Perform one turn where one player is selected as the storyteller and others guess"""
            
        storyteller: Player = self.players[storyteller_idx]
        storyteller_card: Card = storyteller.cards_on_hand[0]  # storyteller chooses a card

        self.cards_on_table.append((storyteller_card, storyteller))
        
        voting: list[tuple[Player, Card]] = []

        if self.debug:
            # Simulate turn in debug mode
            description:str = "Sample popis dlouhý bla bla bla"
            log.info(f"Vypraveč: {storyteller.name}")
            log.info(f"Vybraná karta: {storyteller_card.key}, Popis: {description}")
            for player in self.players:
                if player != storyteller:
                    chosen_card = choice(player.cards_on_hand)
                    logging.info(
                        f"Hrac {player.name} vybral k popisu {description} kartu: {chosen_card.key} a vylozil ji na stul")
                    self.cards_on_table.append((chosen_card, player))

            shuffle(self.cards_on_table)

            # Simulate voting

            for player in self.players:
                if player != storyteller:
                    list_without_players_card = [card for card in self.cards_on_table if card[1] != player]
                    chosen_card = choice(list_without_players_card)[0]
                    log.info(f"Hrac {player.name} hlasoval pro kartu: {chosen_card.key}")
                    voting.append((player, chosen_card))

            self.calculate_scores(voting, storyteller, storyteller_card)

        else:
            # Normal game flow with threads
            description: str = storyteller.make_description(storyteller_card)
            log.info(f"Vypraveč: {storyteller.name}")
            log.info(f"Vybraná karta: {storyteller_card.key}, Popis: {description}")

            threads: list[threading.Thread] = []
            for player in self.players: #https://stackoverflow.com/questions/55529319/how-to-create-multiple-threads-dynamically-in-python
                thread = threading.Thread(target=self.choose_card_thread, args=(player, storyteller, description,))
                threads.append(thread)
                thread.start()

            for thread in threads: # Wait for all threads to finish
                thread.join()

            shuffle(self.cards_on_table)

            # Players except storyteller vote

            vote_threads: list[threading.Thread] = []
            for player in self.players:
                thread = threading.Thread(target=self.vote_thread, args=(player, storyteller, description, voting,))
                vote_threads.append(thread)
                thread.start()

            for thread in vote_threads: # Wait for all threads to finish
                thread.join()

            self.calculate_scores(voting, storyteller, storyteller_card)

        # Show the updated UI
        self.update_ui(storyteller, storyteller_card, description, voting)
        # Remove cards from players' hands, clear cards on the table and give a new card to the players
        self.prepare_next_round()

    def choose_card_thread(self, player: Player, storyteller: Player, description: str) -> None:
        # Thread for player to choose a card
        if player is not storyteller:
            chosen_card = player.choose_card(description, player.cards_on_hand)
            self.cards_on_table.append((chosen_card, player))
            log.info(f"Hráč {player.name} vybral k popisu {description} kartu: {chosen_card.key} a vyložil ji na stůl")

    def vote_thread(self, player: Player, storyteller: Player, description: str, voting: list[tuple[Player, Card]]) -> None:
        # Thread for player to vote for a card
        if player is not storyteller:
            choices = [k[0] for k in self.cards_on_table if k[1] != player] # Cards that are on the table, except the choosing player's card
            chosen_card = player.choose_card(description, choices)
            voting.append((player, chosen_card))
            log.info(f"Hráč {player.name} hlasoval pro kartu: {chosen_card.key}")


    def prepare_next_round(self) -> None:
        # Remove selected cards from players' hands after updating the canvas
        for player in self.players:
            for chosen_card, _ in self.cards_on_table:
                if chosen_card in player.cards_on_hand:
                    player.cards_on_hand.remove(chosen_card)

        self.discard_pile.extend([card for card, player in self.cards_on_table])
        # Adds the discarded cards to the discard pile
        self.cards_on_table.clear()

        if len(self.cards_in_deck) < self.number_of_players:  # If there are not enough cards, add the discard pile to the deck
            shuffle(self.discard_pile)
            self.cards_in_deck.extend(self.discard_pile)
            self.discard_pile.clear()

        for player in self.players:
            player.take_card(self.cards_in_deck.pop(0))

    def calculate_scores(self, voting: list[tuple[Player, Card]], storyteller: Player, storyteller_card: Card) -> None:
        """Calculate scores for the round according to the Dixit rules:
         1. If everyone or no one guessed correctly, add 2 points to everyone except storyteller
         2. If someone guessed correctly, add 3 points to storyteller and 3 points to the correct guesser
         3. Add points to the voters for the number of votes they received"""
        number_of_correct_votes = sum(1 for h in voting if h[1] == storyteller_card)

        if number_of_correct_votes == 0 or number_of_correct_votes == len(self.players) - 1:
            for player in self.players:
                if player != storyteller:
                    log.info(f'Hráč {player.name} získal 2 body')
                    player.score_add(2)
        else:
            storyteller.score_add(3)
            log.info(f'Hráč {storyteller.name} získal 3 body jako vypravěč')
            for player, chosen_card in voting:
                if chosen_card == storyteller_card:
                    log.info(f'Hráč {player.name} získal 3 body')
                    player.score_add(3)

        for card, player in self.cards_on_table:
            if card != storyteller_card:
                for_voted = sum(1 for h in voting if h[1] == card)
                player.score_add(for_voted)
                log.info(f'Hráč {player.name} získal {for_voted} body')

    def preview(self) -> None:
        # Preview the game state before the turn
        self.canvas.update()
        self.start_game_button.destroy()
        self.clear_widget_from_bottom_bar()
        self.canvas.delete('all')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.canvas.create_text(canvas_width // 2, canvas_height // 2,
                               text=f"Vypočítává se tah hráče {self.players[self.index_storyteller].name}",
                               font=("Arial", 24, "bold"))
        footer_text = tk.Label(self.bottom_bar,
                               text=f'Probíha kolo číslo {self.round_number}, vypraveč je {self.players[self.index_storyteller].name}',
                               bg='lightgrey', font=('Arial', 12, 'bold'))
        footer_text.pack(side=tk.BOTTOM, pady=10)

        self.card_images = []  # Clear list for storing images
        for idx, player in enumerate(self.players):
            col = idx % 2   # If idx is even, col is 0, else col is 1
            row = idx // 2  # If idx is even, row is 0, else row is 1
            x_offset = 30 + col * (canvas_width - 590)
            y_offset = 80 + row * (canvas_height -230)

            self.canvas.create_rectangle(x_offset - 10, y_offset - 10, x_offset + 540, y_offset + 130, fill='lightgrey',
                                         outline='')
            self.canvas.create_oval(x_offset - 20, y_offset - 60, x_offset - 5, y_offset - 45,
                                    fill=self.backgrounds[idx % len(self.backgrounds)], outline='')

            description_text = f'{player.name} (Skóre: {player.score})'
            self.canvas.create_text(x_offset, y_offset - 50, text=description_text, anchor='w',
                                    font=('Arial', 16, 'bold'))
            for card_idx, card in enumerate(player.cards_on_hand):
                x = x_offset + card_idx * 90
                y = y_offset
                image = Image.open(card.path)
                image = image.resize((80, 120))
                card_image = ImageTk.PhotoImage(image)
                self.canvas.create_image(x + 40, y + 60, image=card_image)
                self.card_images.append(card_image)  # Store the reference to avoid garbage collection

        self.canvas.update()

    def shuffle_cards(self) -> None:
        for item in self.manager.dict_of_cards:
            self.cards_in_deck.append(self.manager.dict_of_cards[item])
        shuffle(self.cards_in_deck)
        log.info("Karty byly zamíchány")

    def hand_out_cards(self) -> None:
        log.info("Karty byly rozdány")
        # Ensure there are enough cards in the deck
        if len(self.cards_in_deck) < self.number_of_players * self.number_of_cards_per_player:
            raise ValueError("Chyba s kartami, v balíčku jich není dost")

        for player in self.players:
            for i in range(self.number_of_cards_per_player):
                player.take_card(self.cards_in_deck.pop(0))  # Take a card from the deck and give it to the player


    def play_turn(self) -> None:
        # After pressing button, check if game is over or play turn
        self.play_button.config(state=tk.DISABLED)
        self.log_button.config(state=tk.DISABLED)
        self.canvas.update()

        log.info(f'Hraje se kolo číslo {self.round_number}')
        self.play_button.pack(side=tk.RIGHT, padx=10, pady=10)
        max_score = max(player.score for player in self.players)
        if max_score >= 30:
            self.game_end(max_score)
        else:
            self.preview()

            if not self.debug:
                self.turn(self.index_storyteller)
            else:
                self.canvas.after(500, self.turn, self.index_storyteller)
            self.index_storyteller += 1

            if self.index_storyteller >= len(self.players):  # If the index_storyteller is greater than or equal to the number of players,
                self.index_storyteller = 0  # Reset it and increase the round number
                self.round_number += 1
            self.play_button.config(state=tk.NORMAL)
            self.log_button.config(state=tk.NORMAL)

    def update_ui(self, storyteller: Player, storyteller_card: Card, description: str,
                  voting: list[tuple[Player, Card]]) -> None:
        self.clear_widget_from_bottom_bar()
        self.canvas.delete('all')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        self.card_images = []
        for idx, player in enumerate(self.players):
            col = idx % 2   # If idx is even, col is 0, else col is 1
            row = idx // 2  # If idx is even, row is 0, else row is 1
            x_offset = 30 + col * (canvas_width - 590)
            y_offset = 80 + row * (canvas_height -230)

            self.canvas.create_rectangle(x_offset - 10, y_offset - 10, x_offset + 540, y_offset + 130, fill='lightgrey',
                                         outline='')
            self.canvas.create_oval(x_offset - 20, y_offset - 60, x_offset - 5, y_offset - 45,
                                    fill=self.backgrounds[idx % len(self.backgrounds)], outline='')

            description_text = f'{player.name} (Skóre: {player.score})'
            if player == storyteller:
                description_text += f' - {description}'
            self.canvas.create_text(x_offset, y_offset - 50, text=description_text, anchor='w',
                                    font=('Arial', 16, 'bold'))

            # Cards on hand
            for card_idx, card in enumerate(player.cards_on_hand):
                x, y = x_offset + card_idx * 90, y_offset
                image = Image.open(card.path).resize((80, 120))
                card_image = ImageTk.PhotoImage(image)
                self.canvas.create_image(x + 40, y + 60, image=card_image)
                outline_color = self.backgrounds[idx % len(self.backgrounds)] if card == storyteller_card or any(
                    card == k[0] for k in self.cards_on_table) else None
                if outline_color:
                    self.canvas.create_rectangle(x, y, x + 80, y + 120, outline=outline_color, width=5) # Outline chosen cards
                self.card_images.append(card_image)

        # Cards on table
        canvas_width = self.canvas.winfo_width()
        num_cards = len(self.cards_on_table)
        starting_x = (canvas_width - (num_cards * 80 + (num_cards - 1) * 10)) // 2

        for idx, (card, player) in enumerate(self.cards_on_table):
            x, y = starting_x + idx * (80 + 10), self.canvas.winfo_height() // 2
            image = Image.open(card.path).resize((80, 120))
            card_image = ImageTk.PhotoImage(image)
            outline_color = self.backgrounds[self.players.index(player) % len(self.backgrounds)]
            self.canvas.create_rectangle(x, y - 80, x + 80, y + 60, fill=outline_color, outline=outline_color, width=3)
            self.canvas.create_image(x + 40, y, image=card_image)

            self.card_images.append(card_image)
            self.canvas.create_text(x + 40, y - 60, text=player.name, anchor='s', font=('Arial', 10, 'bold'))

            y_offset_text = y + 70
            for voting_player, voted_card in voting:
                if card == voted_card:
                    self.canvas.create_text(x + 40, y_offset_text, text=voting_player.name, anchor='n',
                                            font=('Arial', 10))
                    y_offset_text += 15

        footer_text = tk.Label(self.bottom_bar,
                               text=f'Proběhlo kolo číslo {self.round_number}, vypraveč je {storyteller.name}',
                               bg='lightgrey', font=('Arial', 12, 'bold'))
        footer_text.pack(side=tk.BOTTOM, pady=10)
        self.canvas.update()
    def clear_widget_from_bottom_bar(self)-> None:
        for widget in self.bottom_bar.winfo_children(): # Remove existing labels from the bottom bar
            if isinstance(widget, tk.Label):
                widget.destroy()

    def show_log(self) -> None:
        log_window = tk.Toplevel(self.root)
        log_window.title("Log")

        # Calculate size based on main window
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        window_width = int(main_width * 0.4)
        window_height = int(main_height * 0.8)

        # Calculate position (centered horizontally, 10% from top)
        x = self.root.winfo_x() + (main_width - window_width) // 2
        y = self.root.winfo_y() + int(main_height * 0.1)  # Start at 10% from top

        log_window.geometry(f"{window_width}x{window_height}+{x}+{y}") # positions the log window
        log_window.minsize(300, 400)

        # Create main frame for log window with padding
        log_frame = tk.Frame(log_window)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=0)
        log_frame.grid_columnconfigure(0, weight=1)

        # Create text widget with scrollbars
        text_frame = tk.Frame(log_frame)
        text_frame.grid(row=0, column=0, sticky="nsew")

        log_text = tk.Text(text_frame, wrap=tk.NONE)
        scrollbar_y = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=log_text.yview)
        scrollbar_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=log_text.xview)

        log_text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Grid layout for text and scrollbars
        log_text.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        # Configure grid weights so when resized
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)


        # Load and display log content
        try:
            with open('dixit.log', 'r', encoding='utf-8') as log_file:
                log_content = log_file.read()
                log_text.insert('1.0', log_content)
                log_text.config(state='disabled')  # Make text read-only
        except Exception as e:
            log_text.insert('1.0', f"Problém při načítaní obsahu z logu: {str(e)}")
            log_text.config(state='disabled')

        # Add close button in its own frame at the bottom with more padding
        button_frame = tk.Frame(log_frame)
        button_frame.grid(row=1, column=0, sticky='ew')
        close_button = tk.Button(button_frame, text="Zavřít", command=log_window.destroy)
        close_button.pack(pady=10, padx=5)

    def game_end(self, max_score: int) -> None:
        winners = [hrac for hrac in self.players if hrac.score == max_score]
        winner_names = ', '.join(hrac.name for hrac in winners)
        if len(winners) > 1:
            message = f"Konec hry, vyhráli hráči {winner_names} s {max_score} body."
        else:
            message = f"Konec hry, vyhrál hráč {winner_names} s {max_score} body."
        log.info(message)
        self.display_winner_message(message)

    def display_winner_message(self, message: str) -> None:
        self.clear_widget_from_bottom_bar()
        self.canvas.delete('all')
        self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, text=message,
                                font=("Arial", 24), anchor=tk.CENTER)
        self.play_button.config(state=tk.DISABLED)
        self.canvas.update()


if __name__ == "__main__":
    root = tk.Tk()
    p1 = Player("Petr","učitelka mateřské školky",1)
    p2 = Player("Jana","dítě ve školce",0.9)
    p3 = Player("Josef","učitel fyziky", 0.8)
    p4 = Player("Pavel","neandrtálec", 0.7)
    game = DixitGame([p1,p2,p3,p4], root, debug=True)
    root.mainloop()
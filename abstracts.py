from abc import abstractmethod, ABC
from pydantic import BaseModel


class Card(BaseModel):
    """card with image, path, checksum for verification and encoded picture"""
    key: int
    path: str
    checksum: str
    encoded_picture: str


class AbstractCardManager(ABC):
    """An object, which keeps track of all the cards
    by default loads all images and makes Card instances out of them
    """

    @abstractmethod
    def __init__(self, json_file: str, input_directory: str) -> None:
        self.dict_of_cards: dict[int, Card] = {}
        self.json_file = json_file
        self.input_directory = input_directory
        self.load_cards()
        ...

    @abstractmethod
    def load_cards(self) -> None:
        """Loads all the cards from the json file into dict"""
        ...

    @abstractmethod
    def find_card(self, key: int) -> Card:
        """find a card by key"""
        ...


class AbstractPlayer(ABC):
    """Player"""

    @abstractmethod
    def __init__(self, name: str, nature: str | None, temperature: float | None) -> None:
        """set how the player will behave"""
        self.nature = nature
        self.temperature = temperature
        self.name = name
        self.cards_on_hand: list[Card] = []
        self.score: int = 0
        ...

    @abstractmethod
    def take_card(self, card: Card) -> None:
        """assign card to hand"""
        ...

    @abstractmethod
    def make_description(self, card: Card) -> str:
        """make description for one card"""
        ...

    @abstractmethod
    def choose_card(self, description: str, laid_out_cards: list[Card]) -> Card:
        """look at all cards on the table and choose which one best fits the description"""
        ...

    @abstractmethod
    def score_add(self, number: int) -> None:
        """add score"""
        ...
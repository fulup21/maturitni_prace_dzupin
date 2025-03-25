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
    def _load_cards(self) -> None:
        """Loads all the cards from the json file into dict"""
        ...

    @abstractmethod
    def find_card(self, key: int) -> Card:
        """find a card by key"""
        ...


class AbstractPlayer(ABC):
    """Player"""

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
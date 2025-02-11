"""Module for managing Film Affinity web scrapping"""
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup


@dataclass
class FilmAffinity:
    """Class to create object with all the data"""

    _soup: BeautifulSoup = field(repr=False)
    _mov_title: str = None
    _year: str = None
    _duration: str = None
    _rating: str = None
    _country: str = None
    _director: str = None
    _credits: dict = field(default_factory=dict)
    _actors: str = None
    _producer: str = None
    _genre: str = None
    _synopsis: str = None

    @property
    def mov_title(self):
        """Return title"""
        return self._soup.find("h1", id="main-title").find("span").text.strip()

    @property
    def year(self):
        """Return year"""
        return self._soup.find("dd", itemprop="datePublished").text

    @property
    def duration(self):
        """Return duration"""
        tag = self._soup.find("dd", itemprop="duration")
        if tag is None:
            return "- min."
        return tag.text.strip()

    @property
    def rating(self):
        """Return rating"""
        tag = self._soup.find("div", id="movie-rat-avg")
        if tag is None:
            return "-"
        return tag.text.strip()

    @property
    def country(self):
        """Return country"""
        tag = self._soup.find("span", id="country-img").find("img").attrs["alt"]
        if tag is None:
            return "-"
        return tag.strip()

    @property
    def director(self):
        """Return director"""
        tag = self._soup.find("a", itemprop="url")
        if tag is None:
            return "-"
        return tag.text.strip()

    @property
    def credits(self):
        """Return dict of script, music and photo"""
        dict_credits = {}
        credit = self._soup.dd
        while credit is not None:
            pre_tag = credit.find_previous_sibling("dt")

            if pre_tag.text.strip() == "Guion":
                dict_credits["Guion"] = credit.text.strip()
            if pre_tag.text.strip() == "Música":
                dict_credits["Musica"] = credit.text.strip()
            if pre_tag.text.strip() == "Fotografía":
                dict_credits["Fotografía"] = credit.text.strip()

            credit = credit.find_next_sibling("dd")

        if "Guion" not in dict_credits:
            dict_credits["Guion"] = "-"
        if "Musica" not in dict_credits:
            dict_credits["Musica"] = "-"
        if "Fotografía" not in dict_credits:
            dict_credits["Fotografía"] = "-"

        return dict_credits

    @property
    def actors(self):
        """Return list of actors"""
        credit = self._soup.dd
        while credit is not None:
            pre_tag = credit.find_previous_sibling("dt")

            if pre_tag.text.strip() == "Reparto":
                str_actors = credit.text.strip()

            credit = credit.find_next_sibling("dd")
        return str_actors

    @property
    def producer(self):
        """Return producer"""
        tag = self._soup.find("dd", class_="card-producer")
        if tag is None:
            return "-"
        return tag.text.strip()

    @property
    def genre(self):
        """Return genre"""
        tag = self._soup.find("span", itemprop="genre")
        if tag is None:
            return "-"
        return tag.text.strip()

    @property
    def synopsis(self):
        """Return synopsis"""
        tag = self._soup.find("dd", itemprop="description")
        if tag is None:
            return "-"
        return tag.text.strip()

    def __str__(self) -> str:
        dict_credits = self.credits
        scripter = dict_credits["Guion"]
        music = dict_credits["Musica"]
        photo = dict_credits["Fotografía"]

        string = (
            f"<b>[{self.rating}]</b> <b><i>{self.mov_title}</i></b> <code>({self.duration} {self.year}-{self.country})</code>"
            f"\n\n<code>Dirección:</code>     <b>{self.director}</b>"
            f"\n\n<code>Reparto:</code>     <b>{self.actors}</b>"
            f"\n\n<code>Sinopsis:</code>     <b>{self.synopsis}</b>"
            f"\n\nOtros datos:"
            f"\n     <code>Género:</code>     <b>{self.genre}</b>"
            f"\n     <code>Guión:</code>     <b>{scripter}</b>"
            f"\n     <code>Música:</code>     <b>{music}</b>"
            f"\n     <code>Fotografía:</code>     <b>{photo}</b>"
            f"\n     <code>Productora:</code>     <b>{self.producer}</b>"
        )
        return string

    @staticmethod
    def get_search_url(
        movie: str,
        fromyear: str = "",
        toyear: str = "",
        country: str = "",
        genre: str = "",
        orderby: str = "relevance",
    ) -> str:
        """Method to return the complete URL"""
        search_url = f"https://www.filmaffinity.com/es/advsearch.php?stext={movie}&country={country}&genre={genre}&fromyear={fromyear}&toyear={toyear}&orderby={orderby}"
        return search_url

    @staticmethod
    def get_soup(page: str, head: dict) -> BeautifulSoup:
        """Method to get the soup for a page"""
        _req = requests.get(url=page, headers=head, timeout=10)
        _soup = BeautifulSoup(_req.text, "html.parser")
        return _soup


GENRES = {
    "": "",
    "accion": "AC",
    "animacion": "AN",
    "aventuras": "AV",
    "belico": "BE",
    "ciencia-ficcion": "C-F",
    "negro": "F-N",
    "comedia": "CO",
    "desconocido": "DESC",
    "documental": "DO",
    "drama": "DR",
    "fantastico": "FAN",
    "infantil": "INF",
    "intriga": "INT",
    "musical": "MU",
    "romance": "RO",
    "serie": "TV_SE",
    "terror": "TE",
    "thriller": "TH",
    "western": "WE",
}

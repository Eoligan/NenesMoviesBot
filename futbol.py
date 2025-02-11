"""Module for managing Futbol web scrapping"""
# pylint: disable=invalid-name

from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

NAMES = {
    "Real Madrid": "RMA",
    "Barcelona": "FCB",
    "Atlético": "ATL",
    "Sevilla": "SEV",
    "Betis": "BET",
    "R. Sociedad": "RSO",
    "Villarreal": "VIL",
    "Athletic": "ATH",
    "Valencia": "VAL",
    "Osasuna": "OSA",
    "Celta": "CEL",
    "Rayo": "RAY",
    "Elche": "ELC",
    "Espanyol": "ESP",
    "Getafe": "GET",
    "Mallorca": "MLL",
    "Cádiz": "CAD",
    "Granada": "GRA",
    "Levante": "LEV",
    "Alavés": "ALA",
    "Almería": "ALM",
    "Valladolid": "VLL",
}


@dataclass
class Standings:
    """Dataclass for standings"""

    _soup: BeautifulSoup = field(repr=False)
    _teams: dict[int, dict] = field(default_factory=dict)

    @property
    def teams(self):
        """Return list of team"""

        data = ["pts", "pj", "pg", "pe", "pp", "gf", "gc"]
        elements = self._soup.find_all(
            "th",
            scope="row",
            itemtype="http://schema.org/SportsTeam",
            class_="cont-nombre-equipo",
        )
        for i, ele in enumerate(elements):
            name_team = ele.find("span", itemprop="name").text.strip()
            if NAMES.get(name_team):
                name_team = NAMES[name_team]
            elements_data = ele.find_all_next("td")
            self._teams[i + 1] = {"team": name_team}
            for j, ele_data in enumerate(elements_data[:7]):
                self._teams[i + 1][data[j]] = ele_data.text.strip()

        return self._teams

    def __str__(self) -> str:
        string = ""
        data = ["team", "pts", "pj", "pg", "pe", "pp", "gf", "gc"]

        string += " # "
        string += f"{''.join(data[0]):.3} "
        for i in data[1:]:
            string += f"{''.join(i):.2} "
        string += "\n============================\n"

        for pos, rest_data in self.teams.items():
            if pos == 5 or pos == 7 or pos == 8 or pos == 18:
                string += "----------------------------\n"

            for i, _ in enumerate(rest_data):
                if data[i] == "team":
                    string += f"{pos:>2} {rest_data[data[i]]:3} "
                else:
                    string += f"{rest_data[data[i]]:>2} "
            string += "\n"

        return string

    @staticmethod
    def get_search_url() -> str:
        """Method to return the complete URL"""
        search_url = (
            "https://resultados.as.com/resultados/futbol/primera/clasificacion/"
        )

        return search_url

    @staticmethod
    def get_soup(page: str, head=None) -> BeautifulSoup:
        """Method to get the soup for a page"""
        _req = requests.get(url=page, headers=head, timeout=10)
        _soup = BeautifulSoup(_req.text, "html.parser")
        return _soup


@dataclass
class Football:
    """Dataclass to manage all the football info"""

    _standings: Standings
    # madrid: Madrid()
    # barca: Barca()


# soup = Standings.get_soup(page=Standings.get_search_url(), head=HEADERS)
# clasi = Standings(soup)

# print(clasi)

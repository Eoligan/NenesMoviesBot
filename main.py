"""Bot main application"""
import os
import pickle
import threading
import time
from dataclasses import dataclass

import pyjokes
import requests
import telebot
from bs4 import BeautifulSoup
from flask import Flask, request
from telebot.types import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from waitress import serve

import config as cf
import filetreatment as ft
from filmaffinity import GENRES, FilmAffinity
from futbol import Standings

bot = telebot.TeleBot(cf.API_KEY)  # Instance of bot
web_server = Flask(__name__)  # Instance of web server
data = {}  # Dictionary to save the state of the     bot
for key in cf.DIR:  # Create directory
    try:
        os.mkdir(key)
    except:  # pylint: disable=bare-except
        continue


@web_server.route("/", methods=["POST"])
def webhook():
    """Function for using webhook"""
    # If POST is a JSON
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200


# """ <b>
#  Custom filter for only nenes using the bot
# <b> """


@dataclass
class AreNenes(telebot.SimpleCustomFilter):
    """Control whether the users are nenes"""

    key = "are_nenes"

    @staticmethod
    def check(message: telebot.types.Message) -> bool:  # pylint: disable=W0221
        """Check whether nenes are using the handler"""
        return bot.get_chat(message.chat.id).id in [
            cf.NENE_ID,
            cf.NENA_ID,
            cf.PRUEBA_GROUP_ID,
            cf.PETENOS_GROUP_ID,
        ]


# """ *****************************************************
# Message handler for starting or asking for help to the bot
# ***************************************************** """


def helphelp(commands) -> str:
    """Method when command is /help"""
    response = (
        f"Menú de ayuda:\n"
        f"<b>{commands[0]}</b> | Muestra esta ayuda.\n\n"
        f"<code><b>{commands[0]}</b> nenes</code> | Ayuda para los comandos de manejo de pelis/series\n"
        f"<code><b>{commands[0]}</b> film</code> | Ayuda para el comando film de FilmAffinity\n"
        f"<code><b>{commands[0]}</b> futbol</code> | Ayuda para el comando futbol\n"
        f"\n<b>{commands[6]}</b>\n"
        f"<b>{commands[7]}</b> | Cuenta un chiste.\n"
    )
    return response


def helpnenes(commands) -> str:
    """Method when command called is /help nenes"""
    response = (
        f"<code><b>{commands[1]}</b></code> | Muestra la lista de películas o series.\n"
        f'<code><b>{commands[3]}</b></code> | Añade "nombre" en películas o series.\n'
        f'<code><b>{commands[4]}</b></code> | Edita "nombre" en película o serie.\n'
        f'<code><b>{commands[5]}</b></code> | Borra "nombre" en película o serie.\n'
        f'<code><b>{commands[2]}</b></code> | Busca "nombre" en películas o series.\n'
        f"<code><b>{commands[8]}</b></code> | Lista los 10 últimos en películas o series.\n"
        f"\nArgumentos:   <b><code>-m   -mt   -s   -st</code></b>\n"
    )
    return response


def helpfilm() -> str:
    """Method when command calles is /help film or /film"""
    response = (
        "<b>Modo de uso:</b> <code>/film [peli] [opciones]</code>"
        "\n\nOpciones:"
        "\n        <code>-from [año en formato: aaaa]</code> | Desde el año"
        "\n        <code>-to [año en formato: aaaa]</code> | Hasta el año"
        "\n        <code>-country [código de dos letras de país]</code> | Según el país"
        "\n        <code>-genre [género]</code> | Según el género"
        "\n                (accion, animacion, aventuras, ciencia-ficcion,"
        "\n                negro, comedia, desconocido, documental, drama,"
        "\n                fantastico, infantil, intriga, musical, serie,"
        "\n                terror, thriller, western)"
        "\n        <code>-orderby [relevance | year]</code> | Ordenar por relevancia o año"
    )
    return response


def helpfutbol() -> str:
    """Method when command called is /help futbol or /futbol"""
    response = (
        "<b>Modo de uso:</b> <code>/futbol [opción]</code>"
        "\n\nOpciones:"
        "\n        <code>clasi</code> | Muestra la clasificación"
        "\n        <code>madrid</code> | Muestra los partidos del Madrid"
        "\n        <code>barca</code> | Muestra los partidos  del Barça"
    )
    return response


@bot.message_handler(are_nenes=True, commands=["start", "help"])
def help_(message):
    """To show help"""
    commands = (
        "/help",
        "/list",
        "/find",
        "/add",
        "/edit",
        "/del",
        "/hola",
        "/chiste",
        "/last",
        "/film",
    )
    response = ""
    args = message.text.split()

    if len(args) < 2:
        response = helphelp(commands)

    else:
        if args[1] == "nenes":
            response = helpnenes(commands)
        elif args[1] == "film":
            response = helpfilm()
        elif args[1] == "futbol" or args[1] == "fútbol":
            response = helpfutbol()
        else:  # En caso de argumento incorrecto
            response = "Argumento incorrecto"
    bot.send_message(
        message.chat.id,
        response,
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )


@bot.message_handler(are_nenes=True, commands=["chiste"])
def chiste(message):
    """Manda una chiste"""
    joke = pyjokes.get_joke(language="es", category="all")
    bot.send_message(message.chat.id, joke)


# """ Methods to obtain the correct file to work with """


def check_file(arg) -> str:
    """Checking which is the file"""
    match arg[0]:
        case "-m" | "movies":
            return cf.MOVIES
        case "-mt" | "movies to see":
            return cf.MOVIES_TO_SEE
        case "-s" | "series":
            return cf.SERIES
        case "-st" | "series to see":
            return cf.SERIES_TO_SEE
        case _:
            return None


def get_file(message) -> str:
    """Check if the arguments are valid and return the path of the file to use"""
    arg = message.text.split()

    if not arg[1:]:
        return None

    file = check_file(arg[1:])
    res = file

    match arg[0]:
        case "/list" | "/last":
            pass
        case "/find" | "/add":
            if len(arg) < 3:
                res = None
        case "/del":
            if len(arg) < 3:
                res = None
            if arg[2] == "-last":
                res = file
            if not arg[2].isdigit():
                res = None
        case "/edit":
            if len(arg) < 4 or not arg[2].isdigit():
                res = None

    return res


# """ *****************************************************
# Message handlers for bot sending messages to user/group algo
# ***************************************************** """

# """HANDLE FILE BUTTON (FOR EVERYONE)"""


def buttons_ask_file(message) -> str:
    """Function to handle the file button that is the same for every command"""
    file_button = ReplyKeyboardMarkup(
        one_time_keyboard=True,
        input_field_placeholder=("Elige un fichero"),
        resize_keyboard=True,
    )
    file_button.add("Movies", "Movies to see", "Series", "Series to see", row_width=2)

    msg = bot.send_message(
        message.chat.id, "Elige el fichero:", reply_markup=file_button
    )
    return msg


# """COMMAND: LIST / LAST"""


@bot.message_handler(are_nenes=True, commands=["list"])
def list_command(message):
    """Command list for any movie/serie"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dict of dicts of ID. Every person in different dict
    data[message.chat.id]["command"] = "list"

    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, handler_list_last)
    else:  # Or only with the full text command
        lst = ft.list_(file)
        bot.send_message(message.chat.id, "".join(str(i) for i in lst))


@bot.message_handler(are_nenes=True, commands=["last"])
def last_command(message):
    """Command last for last 10 movies/series"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dictionary of dictionary of ID.
    data[message.chat.id]["command"] = "last"
    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, handler_list_last)
    else:
        lst = ft.find_last(file)
        bot.send_message(message.chat.id, "".join(str(i) for i in lst))


def handler_list_last(message):
    """Last step for control list with buttons"""
    file = []
    file.append(message.text.lower())
    file = check_file(file)
    if file is None:
        bot.send_message(
            message.chat.id,
            "Ese fichero no existe, pecador de la pradera!!",
            reply_markup=ReplyKeyboardRemove,
        )
    else:
        lst = ft.list_(file)
        if data[message.chat.id]["command"] == "last":
            lst = ft.find_last(file)
        bot.send_message(
            message.chat.id,
            "".join(str(i) for i in lst),
            reply_markup=ReplyKeyboardRemove(),
        )
    data.clear()


# """COMMAND: FIND / ADD"""


@bot.message_handler(are_nenes=True, commands=["find"])
def find_command(message):
    """Command list for any movie/serie"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dictionary of dictionary of ID.
    data[message.chat.id]["command"] = "find"
    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, find_add_ask_name)
    else:
        error = "No se ha encontrado."
        lst = ft.find_(file, message.text.split()[2:])
        bot.send_message(
            message.chat.id, [error if not lst else "".join(str(i) for i in lst)]
        )


@bot.message_handler(are_nenes=True, commands=["add"])
def add_command(message):
    """Command add for any movie/serie"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dictionary of dictionary of ID.
    data[message.chat.id]["command"] = "add"

    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, find_add_ask_name)
    else:
        file_name = ft.which_file(file)
        req = message.text.split()  # Get the movie to add
        data[message.chat.id]["movie"] = " ".join(list(req[2:]))
        movie = data[message.chat.id]["movie"]
        pos = ft.len_(file)

        ft.add(file, movie, pos + 1)
        bot.send_message(
            message.chat.id,
            f'{file_name.capitalize().replace("_", " ")} #{pos+1} añadida:   {movie}',
        )


def find_add_ask_name(message):
    """Next-step for asking name argument in find with buttons"""
    file = []
    file.append(message.text.lower())
    file = check_file(file)
    data[message.chat.id]["file"] = file

    if file is None:
        bot.send_message(
            message.chat.id,
            "Ese fichero no existe, pecador de la pradera!!",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        if data[message.chat.id]["command"] == "find":
            msg = bot.send_message(
                message.chat.id,
                "Escribe la peli/serie a buscar:",
                reply_markup=ForceReply(),
            )
        if data[message.chat.id]["command"] == "add":
            msg = bot.send_message(
                message.chat.id,
                "Escribe la peli/serie a añadir: ",
                reply_markup=ForceReply(),
            )
        bot.register_next_step_handler(msg, handler_find_add)


def handler_find_add(message):
    """Last step for control find with buttons"""
    error = "No se ha encontrado."
    file = data[message.chat.id]["file"]

    if data[message.chat.id]["command"] == "add":
        file_name = ft.which_file(file)
        movie = message.text
        pos = ft.len_(file)

        ft.add(file, movie, pos + 1)
        bot.send_message(
            message.chat.id,
            f'{file_name.capitalize().replace("_", " ")} #{pos+1} añadida:   {movie}',
        )

    if data[message.chat.id]["command"] == "find":
        lst = ft.find_(data[message.chat.id]["file"], message.text.split())
        bot.send_message(
            message.chat.id, [error if not lst else "".join(str(i) for i in lst)]
        )
    data.clear()


# """COMMAND: EDIT"""


@bot.message_handler(are_nenes=True, commands=["edit"])
def edit_command(message):
    """Command edit for any movie/serie"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dictionary of dictionary of ID.
    data[message.chat.id]["command"] = "add"

    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, edit_ask_name)
    else:
        file_name = ft.which_file(file)

        req = message.text.split()
        movie = " ".join(list(req[3:]))
        pos = int(req[2])

        length = ft.len_(file)
        if pos < 1 or pos > length:
            bot.send_message(message.chat.id, f"Error: la película {pos} no existe.")
            return 1

        ft.edit(file, movie, pos)
        bot.send_message(
            message.chat.id,
            f'{file_name.capitalize().replace("_", " ")} #{pos} editada:   {movie}',
        )


def edit_ask_name(message):
    """Next-step for asking name argument in find with buttons"""
    file = []
    file.append(message.text.lower())
    file = check_file(file)
    data[message.chat.id]["file"] = file

    if file is None:
        bot.send_message(
            message.chat.id,
            "Ese fichero no existe, pecador de la pradera!!",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            "Escribe el número de peli/serie a editar:",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(msg, edit_ask_num)


def edit_ask_num(message):
    """Step to control the number of movie to edit"""
    file = data[message.chat.id]["file"]
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Error: no me has puesto un número, perraca!")
        return

    num_movie = int(message.text)
    length = ft.len_(file)
    if num_movie < 1 or num_movie > length:
        bot.send_message(message.chat.id, f"Error: la película {num_movie} no existe.")
        return 1

    data[message.chat.id]["num_movie"] = num_movie

    msg = bot.send_message(
        message.chat.id, "Escribe el nuevo nombre:", reply_markup=ForceReply()
    )
    bot.register_next_step_handler(msg, handler_edit)


def handler_edit(message):
    """Last step for control edit with buttons"""
    new_name_movie = message.text
    file = data[message.chat.id]["file"]
    pos = data[message.chat.id]["num_movie"]

    file_name = ft.which_file(file)

    ft.edit(file, new_name_movie, pos)
    bot.send_message(
        message.chat.id,
        f'{file_name.capitalize().replace("_", " ")} #{pos} editada:   {new_name_movie}',
    )
    data.clear()


# """COMMAND: DEL"""


@bot.message_handler(are_nenes=True, commands=["del"])
def del_command(message):
    """Command del for any movie/serie"""
    file = get_file(message)
    data[message.chat.id] = {}  # Dict of dicts of ID. Every person in different dict
    data[message.chat.id]["command"] = "del"

    if file is None:  # Controlling commands with buttons
        response = buttons_ask_file(message)
        bot.register_next_step_handler(response, del_ask_name)
    else:
        file_name = ft.which_file(file)
        req = message.text.split()

        if req[2].isdigit():  # Argument 'number'
            pos = int(req[2])
            length = ft.len_(file)

            if pos < 1 or pos > length:
                bot.send_message(
                    message.chat.id,
                    f'Error: {file_name.capitalize().replace("_", " ")} #{pos} no existe.',
                )
                return 1

            movie = ft.find_pos(file, pos)
            ft.del_(file, pos)

        else:  # Argument '-last'
            pos = ft.len_(file)
            movie = ft.find_pos(file, pos)
            ft.del_last(file)

        bot.send_message(
            message.chat.id,
            f'{file_name.capitalize().replace("_", " ")} #{movie[0]} borrada:   {movie[1]}',
        )


def del_ask_name(message):
    """Step to control number of movie/serie to delete"""
    file = []
    file.append(message.text.lower())
    file = check_file(file)
    data[message.chat.id]["file"] = file

    if file is None:
        bot.send_message(
            message.chat.id,
            "Ese fichero no existe, pecador de la pradera!!",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        file_button = ReplyKeyboardMarkup(
            one_time_keyboard=True,
            input_field_placeholder=(
                "Escribe un númer de peli/serie a borrar o pulsa el botón para borrar último"
            ),
            resize_keyboard=True,
        )
        file_button.add("-last", row_width=1)

        msg = bot.send_message(
            message.chat.id,
            "Escribe un númer de peli/serie a borrar o pulsa el botón para borrar último:",
            reply_markup=file_button,
        )
        bot.register_next_step_handler(msg, handler_del)


def handler_del(message):
    """Last step to handle del with buttons"""
    file = data[message.chat.id]["file"]
    file_name = ft.which_file(file)
    param_movie = message.text

    if not param_movie.isdigit() and param_movie != "-last":  # Handle bad arguments
        bot.send_message(
            message.chat.id,
            "Error: no me has puesto un número o argumento '-last', perraca!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return 1

    if param_movie.isdigit():  # Argument 'number'
        num_movie = int(param_movie)
        length = ft.len_(file)

        if num_movie < 1 or num_movie > length:
            bot.send_message(
                message.chat.id,
                f'Error: {file_name.capitalize().replace("_", " ")} #{num_movie} no existe.',
                reply_markup=ReplyKeyboardRemove(),
            )
            return 1

        movie = ft.find_pos(file, num_movie)
        ft.del_(file, num_movie)

    else:  # Argument '-last'
        num_movie = ft.len_(file)
        movie = ft.find_pos(file, num_movie)
        ft.del_last(file)

    bot.send_message(
        message.chat.id,
        f'{file_name.capitalize().replace("_", " ")} #{movie[0]} borrada:   {movie[1]}',
        reply_markup=ReplyKeyboardRemove(),
    )


# """ *****************************************************
# FilmAffinity command
# ***************************************************** """


def check_film_arguments(req: list) -> dict:
    """Check arguments for command film and return a dictionary with values changed"""
    film_args = {
        "movie": "",
        "fromyear": "",
        "toyear": "",
        "country": "",
        "genre": "",
        "orderby": "relevance",
    }
    for i, opt in reversed(list(enumerate(req))):
        match opt:
            case "-from":
                film_args["fromyear"] = req[i + 1]
                req.pop(i)
                req.pop(i)
            case "-to":
                film_args["toyear"] = req[i + 1]
                req.pop(i)
                req.pop(i)
            case "-country":
                film_args["country"] = req[i + 1]
                req.pop(i)
                req.pop(i)
            case "-genre":
                film_args["genre"] = req[i + 1]
                req.pop(i)
                req.pop(i)
            case "-orderby":
                film_args["orderby"] = req[i + 1]
                req.pop(i)
                req.pop(i)
    film_args["movie"] = " ".join(req[1:])
    return film_args


@bot.message_handler(are_nenes=True, commands=["film"])
def film(message):
    """Command film for searching a movie in FilmAffinity"""
    req = message.text.split()
    if not req[1:]:
        response = helpfilm()
        bot.send_message(message.chat.id, response, parse_mode="html")
        return 1

    film_args = check_film_arguments(req)

    url = FilmAffinity.get_search_url(
        movie=film_args["movie"],
        fromyear=film_args["fromyear"],
        toyear=film_args["toyear"],
        country=film_args["country"],
        genre=GENRES[film_args["genre"]] if GENRES.get(film_args["genre"]) else "",
        orderby=film_args["orderby"],
    )

    request_url = requests.get(url=url, headers=cf.HEADERS, timeout=10)
    if request_url.status_code != 200:
        bot.send_message(
            message.chat.id,
            f"Error al buscar: {request_url.status_code} {request_url.reason}",
        )
        return 1

    soup = BeautifulSoup(request_url.text, "html.parser")

    if soup.find("b", text="No se han encontrado coincidencias."):
        bot.send_message(
            message.chat.id,
            f'No se han encontrado resultados. - {film_args["movie"]}? me estás vacilando?',
        )
        return 1

    elements = soup.find_all("div", class_="mc-title")
    elements_list = []

    for i, element in enumerate(elements):
        try:
            id_ = i + 1
            year = element.text[-6:].strip().split(")")[0]
            title = element.find("a").attrs["title"].strip()
            link = element.find("a").attrs["href"].strip()

            if [str(id_), year, title, link] in elements_list:
                continue
            elements_list.append([str(id_), year, title, link])
        except IndexError:
            continue
    show_page(elements_list, message.chat.id)


def show_page(movie_list, chatid, pag=0, messageid=None):
    """Create or edit a page message"""
    markup = InlineKeyboardMarkup(row_width=cf.MAX_WIDTH_ROW)
    pre_page_button = InlineKeyboardButton("⬅️", callback_data="pre")
    close_button = InlineKeyboardButton("❌", callback_data="close")
    next_page_button = InlineKeyboardButton("➡️", callback_data="next")
    start_ = pag * cf.N_RES_PAG
    end_ = start_ + cf.N_RES_PAG
    # controlamos que se muestre correctamente el número de páginas final
    if end_ > len(movie_list):
        end_ = len(movie_list)

    text_ = f"<i>Resultados {start_+1}/{end_} de {len(movie_list)}</i>\n\n"

    ncount = 1
    choose_buttons = []
    data_page = {"pag": 0, "list": movie_list}
    for item in movie_list[start_:end_]:
        button_id = str(start_ + ncount)
        choose_buttons.append(
            InlineKeyboardButton(
                str(start_ + ncount),
                callback_data=f"chosen_movie:{button_id}",
            )
        )
        text_ += f"[<b>{start_ + ncount}</b>] <a href='{item[3]}'>{item[1]} - {item[2]}</a>\n"
        ncount += 1

    markup.add(*choose_buttons)
    markup.row(pre_page_button, close_button, next_page_button)

    if messageid:
        bot.edit_message_text(
            text_,
            chatid,
            messageid,
            reply_markup=markup,
            parse_mode="html",
            disable_web_page_preview=True,
        )
    else:
        res = bot.send_message(
            chatid,
            text_,
            reply_markup=markup,
            parse_mode="html",
            disable_web_page_preview=True,
        )
        messageid = res.message_id
        pickle.dump(data_page, open(f"{cf.DIR['searches']}{chatid}_{messageid}", "wb"))


@bot.callback_query_handler(func=lambda x: x.data.startswith("chosen_movie:"))
def chosen_mov(call):
    """Manage the behaviour of the button to show movie"""
    chatid = call.message.chat.id
    messageid = call.message.id
    id_ = int(call.data.split(":")[1]) - 1
    data_page = pickle.load(open(f"{cf.DIR['searches']}{chatid}_{messageid}", "rb"))

    url = data_page["list"][id_][3]
    mov = FilmAffinity(FilmAffinity.get_soup(page=url, head=cf.HEADERS))
    bot.send_message(chatid, str(mov), parse_mode="html")


@bot.callback_query_handler(func=lambda x: True)
def callback_answer_buttons(call):
    """Manage the behaviour of the buttons"""
    chatid = call.message.chat.id
    messageid = call.message.id

    if call.data == "close":
        bot.delete_message(chatid, messageid)
        return

    data_page = pickle.load(open(f"{cf.DIR['searches']}{chatid}_{messageid}", "rb"))
    if call.data == "pre":
        # si ya estamos en la primera página
        if data_page["pag"] == 0:
            bot.answer_callback_query(call.id, "Ya estás en la primera página")
        else:
            data_page["pag"] -= 1
            pickle.dump(
                data_page, open(f"{cf.DIR['searches']}{chatid}_{messageid}", "wb")
            )
            show_page(data_page["list"], chatid, data_page["pag"], messageid)
        return
    if call.data == "next":
        # si ya estamos en la última página
        if data_page["pag"] * cf.N_RES_PAG + cf.N_RES_PAG >= len(data_page["list"]):
            bot.answer_callback_query(call.id, "Ya estás en la última página")
        else:
            data_page["pag"] += 1
            pickle.dump(
                data_page, open(f"{cf.DIR['searches']}{chatid}_{messageid}", "wb")
            )
            show_page(data_page["list"], chatid, data_page["pag"], messageid)
        return


# """ *****************************************************
# Futbol command
# ***************************************************** """
@bot.message_handler(are_nenes=True, commands=["futbol", "fútbol"])
def futbol(message):
    """Command futbol"""
    req = message.text.split()
    if not req[1:]:
        response = helpfutbol()
        bot.send_message(message.chat.id, response, parse_mode="html")
        return 1

    opt = req[1]

    match opt:
        case "clasi":
            futbol_standing(message.chat.id)
        case "madrid":
            pass
        case "barca":
            pass
        case _:
            bot.send_message(message.chat.id, "No existe esa opción elegida.")


def futbol_standing(chatid):
    """When chosen option is clasi"""
    url = Standings.get_search_url()
    request_url = requests.get(url=url, headers=cf.HEADERS, timeout=10)
    if request_url.status_code != 200:
        bot.send_message(
            chatid,
            f"Error al leer la clasificación: {request_url.status_code} {request_url.reason}",
        )
        return 1

    clasi = Standings(Standings.get_soup(page=url, head=cf.HEADERS))

    bot.send_message(chatid, f"<pre>{clasi}</pre>", parse_mode="html")


# """ Methods to control web-server"""


def polling():
    """Initiate polling when running in local"""
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()


def start_web_server():
    """Initiate web-server when running in web"""
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=cf.APP_URL)
    serve(
        web_server,
        host="0.0.0.0",
        port=os.environ.get("PORT", 5000),
    )


# """ *****************************************************
# Main
# ***************************************************** """


def main():
    """Main"""
    bot.set_my_commands(
        [
            telebot.types.BotCommand("/help", "Menú de comandos"),
            telebot.types.BotCommand("/list", "Listar pelis"),
            telebot.types.BotCommand("/add", "Añadir pelis"),
            telebot.types.BotCommand("/edit", "Editar pelis"),
            telebot.types.BotCommand("/del", "Borrar pelis"),
            telebot.types.BotCommand("/find", "Buscar pelis"),
            telebot.types.BotCommand("/last", "Buscar últimas 10 pelis"),
        ]
    )
    bot.add_custom_filter(AreNenes())

    if os.environ.get("DYNO_RAM"):
        thread = threading.Thread(
            name="web_server_thread", target=start_web_server
        )  # Initiate web-server if heroku
    else:
        thread = threading.Thread(
            name="polling_thread", target=polling
        )  # If not heroku, use polling (local)
    thread.start()


if __name__ == "__main__":
    main()

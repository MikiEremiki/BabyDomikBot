import logging
import datetime
from typing import (
    Tuple,
    Dict,
    Any,
    List,
    Union
)

from telegram import (
    Bot,
    Update,
    InlineKeyboardButton,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeChatAdministrators,
)
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import googlesheets
from settings import (
    RANGE_NAME,
    COMMAND_DICT,
    ADMIN_GROUP_ID,
    ADMIN_CHAT_ID,
    ADMIN_ID,
    CHAT_ID_GROUP_ADMIN,
)


def load_data() -> Tuple[
                    Dict[str, str],
                    Dict[str, int],
                    Dict[int, str],
                    Dict[str, str]
]:
    """
    Возвращает 4 словаря из гугл-таблицы с листа "База спектаклей"
    Проводит фильтрацию по дате, все прошедшие даты исключаются из выборки

    dict_of_shows -> Все спектакли со всеми данными
    dict_of_name_show -> key: str (название спектакля), item: int
    dict_of_name_show_flip -> key: int, item: str (название спектакля)
    dict_of_date_show -> key: str (дата спектакля), item: int (номер спектакля)

    :return: dict, dict, dict, dict
    """
    data_of_dates = googlesheets.get_data_from_spreadsheet(
        RANGE_NAME['База спектаклей_дата']
    )

    # Исключаем из загрузки в data спектакли, у которых дата уже прошла
    first_row = 2
    date_now = datetime.datetime.now().date()
    for i, item in enumerate(data_of_dates[1:]):
        date_tmp = item[0].split()[0] + f'.{date_now.year}'
        date_tmp = datetime.datetime.strptime(date_tmp, f'%d.%m.%Y').date()
        if date_tmp >= date_now:
            first_row += i
            break

    data = googlesheets.get_data_from_spreadsheet(
        RANGE_NAME['База спектаклей_'] + f'A{first_row}:I'
    )
    logging.info('Данные загружены')

    dict_of_shows = {}
    dict_of_name_show = {}
    dict_of_name_show_flip = {}
    dict_of_date_show = {}
    j = 0
    for i, item in enumerate(data):
        i += first_row - 1
        dict_of_shows[i + 1] = {
            'name_of_show': item[0],
            'date': item[1],
            'time': item[2],
            'total_children_seats': item[3],
            'available_children_seats': item[4],
            'non_confirm_children_seats': item[5],
            'total_adult_seats': item[6],
            'available_adult_seats': item[7],
            'non_confirm_adult_seats': item[8],
        }

        if item[0] not in dict_of_name_show:
            j += 1
            dict_of_name_show.setdefault(item[0], j)
            dict_of_name_show_flip.setdefault(j, item[0])

        date_now = datetime.datetime.now().date()
        date_tmp = item[1].split()[0] + f'.{date_now.year}'
        date_tmp = datetime.datetime.strptime(date_tmp, f'%d.%m.%Y').date()

        if date_tmp >= date_now and item[1] not in dict_of_date_show:
            dict_of_date_show.setdefault(item[1], dict_of_name_show[item[0]])

    return (
        dict_of_shows,
        dict_of_name_show,
        dict_of_name_show_flip,
        dict_of_date_show,
    )


def load_option_buy_data() -> Dict[str, Any]:
    dict_of_option_for_reserve = {}
    data = googlesheets.get_data_from_spreadsheet(RANGE_NAME['Варианты стоимости'])
    logging.info("Данные стоимости броней загружены")

    for item in data[1:]:
        if len(item) == 0:
            break
        dict_of_option_for_reserve[int(item[0])] = {
            'name': item[1],
            'price': int(item[2]),
            'quality_of_children': int(item[3]),
            'quality_of_adult': int(item[4]),
            'flag_individual': bool(int(item[5])),
        }

    return dict_of_option_for_reserve


def load_clients_data(name: str, date: str, time: str) -> List[List[str]]:
    data_clients_data = []
    first_colum = googlesheets.get_data_from_spreadsheet(
        RANGE_NAME['База клиентов']
    )
    first_row = googlesheets.get_data_from_spreadsheet(
        RANGE_NAME['База клиентов__']
    )
    sheet = (
        RANGE_NAME['База клиентов_'] +
        f'!R1C1:R{len(first_colum)}C{len(first_row[0])}'
    )
    data = googlesheets.get_data_from_spreadsheet(sheet)

    for item in data[1:]:
        if (
            item[6] == name and
            item[7] == date and
            item[8] == time
        ):
            data_clients_data.append(item)

    return data_clients_data


def add_btn_back_and_cancel() -> List[object]:
    """

    :return: List
    """
    button_back = InlineKeyboardButton(
        "Назад",
        callback_data='Назад'
    )
    button_cancel = InlineKeyboardButton(
        "Отменить",
        callback_data='Отменить'
    )
    return [button_back, button_cancel]


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(
        f'{update.effective_user.id}: '
        f'{update.effective_user.full_name}\n'
        f'Вызвал команду echo'
    )
    text = ' '.join([
        str(update.effective_chat.id),
        'from',
        str(update.effective_user.id)
    ])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )


async def delete_message_for_job_in_callback(
        context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.delete_message(
        chat_id=context.job.chat_id,
        message_id=context.job.data
    )


def replace_markdown_v2(text: str) -> str:
    text = text.replace('_', '\_')
    text = text.replace('*', '\*')
    text = text.replace('[', '\[')
    text = text.replace(']', '\]')
    text = text.replace('(', '\(')
    text = text.replace(')', '\)')
    text = text.replace('~', '\~')
    text = text.replace('`', '\`')
    text = text.replace('>', '\>')
    text = text.replace('#', '\#')
    text = text.replace('+', '\+')
    text = text.replace('-', '\-')
    text = text.replace('=', '\=')
    text = text.replace('|', '\|')
    text = text.replace('{', '\{')
    text = text.replace('}', '\}')
    text = text.replace('.', '\.')
    text = text.replace('!', '\!')

    return text


async def set_menu(bot: Bot) -> Bot:
    group_commands = [
        BotCommand(COMMAND_DICT['LIST'][0], COMMAND_DICT['LIST'][1]),
        BotCommand(COMMAND_DICT['LOG'][0], COMMAND_DICT['LOG'][1]),
    ]
    admin_commands = [
        BotCommand(COMMAND_DICT['RESERVE'][0], COMMAND_DICT['RESERVE'][1]),
        BotCommand(COMMAND_DICT['LIST'][0], COMMAND_DICT['LIST'][1]),
        BotCommand(COMMAND_DICT['LOG'][0], COMMAND_DICT['LOG'][1]),
    ]

    for chat_id in ADMIN_GROUP_ID:
        try:
            await bot.set_my_commands(
                commands=group_commands,
                scope=BotCommandScopeChatAdministrators(chat_id=chat_id)
            )
        except BadRequest:
            continue
    for chat_id in ADMIN_CHAT_ID:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=chat_id)
            )
        except BadRequest:
            continue

    return bot


async def send_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id in ADMIN_ID:
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document='log.txt'
            )
        except FileExistsError:
            logging.info('Файл логов не найден')


async def send_message_to_admin(
        text: str,
        message_id: Union[int, str],
        context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        await context.bot.send_message(
            chat_id=CHAT_ID_GROUP_ADMIN,
            text=text,
            reply_to_message_id=message_id
        )
    except BadRequest:
        logging.info(": ".join(
            [
                'Для пользователя',
                str(context.user_data['user'].id),
                str(context.user_data['user'].full_name),
                'сообщение на которое нужно ответить, удалено'
            ],
        ))
        await context.bot.send_message(
            chat_id=CHAT_ID_GROUP_ADMIN,
            text=text,
        )

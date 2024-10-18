import json
import time
from typing import Dict, List, Set
from rss_processors.feed_processor import (
    Article,
    ArxivRSSParser,
    DailyHFRSSParser,
    RSSFeedProcessor,
)
import telebot
from telebot import types
from langchain_openai import ChatOpenAI
import random
from threading import Thread
import schedule
import os

model = ChatOpenAI(
    model_name="gpt-3.5-turbo-0125",
    openai_api_key=os.environ.get("GPT",""),
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Добавляем словарь для хранения статей пользователя
user_articles: Dict[int, List[Article]] = {}


RSS_SOURCES = {
    "HuggingFace Daily pappers": "https://jamesg.blog/hf-papers.xml",
    "arXiv AI": "https://arxiv.org/rss/cs.AI",
    "arXiv ML": "https://arxiv.org/rss/cs.LG",
}
#TOPICS = ["NLP", "CV", "Generative Models"]

USER_CHAT_ID = 356509850
CHANNEL_ID = -1001569150954
TELEGRAM_TOKEN = os.environ.get("TG","")
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_subscriptions: Dict[int, Set[str]] = {}
PREPARE_PUB = None
PREPARE_PUB_PROMPT = "Напиши цитату из культовых мультфильмов или ситкомов c подписью: "

# Инициализация процессора RSS-ленты
rss_processor = RSSFeedProcessor()
rss_processor.register_feed("arXiv AI", RSS_SOURCES["arXiv AI"], ArxivRSSParser())
rss_processor.register_feed("arXiv ML", RSS_SOURCES["arXiv ML"], ArxivRSSParser())
rss_processor.register_feed(
    "HuggingFace Daily pappers",
    RSS_SOURCES["HuggingFace Daily pappers"],
    DailyHFRSSParser(),
)



def escape_markdown(text: str) -> str:
    if not text:
        return ''
    escape_chars = r'\_[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])



# Функции для сохранения и загрузки данных
SUBSCRIPTIONS_FILE = "user_subscriptions.json"
TOPICS_FILE = "user_topics.json"

@bot.message_handler(commands=["set_prompt"])
def set_prompt(message):
    global PREPARE_PUB_PROMPT
    if message.chat.id == int(USER_CHAT_ID):
        new_prompt = message.text[len("/set_prompt ") :].strip()
        if new_prompt:
            PREPARE_PUB_PROMPT = new_prompt
            bot.reply_to(
                message,
                f"Промпт обновлён. Новый текст для публикации:\n\n{PREPARE_PUB_PROMPT}",
            )
        else:
            bot.reply_to(
                message,
                "Пожалуйста, укажите новый текст для промпта после команды /set_prompt.",
            )
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")


def send_remind():
    global PREPARE_PUB
    if PREPARE_PUB_PROMPT:
        joke = escape_markdown(model.invoke(PREPARE_PUB_PROMPT).content).replace(
            "\.", "."
        )
        bot.send_message(USER_CHAT_ID, f"prepare: {joke}")
        PREPARE_PUB = joke
    else:
        bot.send_message(USER_CHAT_ID, "Задайте : set_prompt")


def send_daily_joke():
    global PREPARE_PUB
    PREPARE_PUB = escape_markdown(
        model.invoke(
            "Придумай оригинальный анекдот про нейросети, прогрммирование: "
        ).content
    ).replace("\.", ".")
    bot.send_message(USER_CHAT_ID, f"Шутка дня: {PREPARE_PUB}")


def schedule_runner():
    schedule.every().day.at("10:33").do(
        send_remind
    )  # Отправка текста каждый день в 09:00
    schedule.every().day.at("17:34").do(
        send_daily_joke
    )  # Отправка анекдота каждый день в 10:00
    while True:
        schedule.run_pending()
        time.sleep(1)


@bot.message_handler(commands=["gpt"])
def meme(message):
    new_prompt = message.text[len("/gpt ") :].strip()
    anecdot = escape_markdown(model.invoke(new_prompt).content).replace("\.", ".")
    a = random.choice([0,1,2,3,4,5,6,7,8,9,10])
    if a ==1:
        bot.send_message(message.chat.id, "😁😁😁😁 ГООООЛ СЛИИИТ 😁😁😁😁")
    else:
        bot.send_message(message.chat.id, f"{get_random_kind_emoji()} {new_prompt}: {anecdot}")
        

# Функция для получения случайного "доброго" эмодзи
def get_random_kind_emoji() -> str:
    kind_emojis = [
        "😊",
        "😁",
        "😄",
        "😍",
        "🥰",
        "😇",
        "🤗",
        "😸",
        "😺",
        "🌞",
        "💖",
        "✨",
        "🌈",
        "🍀",
        "🎉",
        "🎈",
        "😵‍💫",
        "🤧",
        "💩",
        "👻",
        "🤖",
        "👾",
        "👽",
        "☠️",
        "🖐🏻",
        "🩱",
        "👠",
        "👡",
        "🧦",
        "🥾",
        "🧢",
        "👑",
        "💍",
        "🎒",
        "🥽",
        "🌂",
        "👛",
        "⛑️",
        "🎓",
        "🧤",
        "🙈",
        "🙉",
        "🙊",
        "🐵",
        "🐔",
        "🦉",
        "🐥",
        "🫎",
        "🦄",
        "🦋",
        "🕸️",
        "🪰",
        "🪲",
        "🪳",
        "🦟",
        "🦗",
        "🐍",
        "🐙",
        "🦕",
        "🦞",
        "🐬",
        "🐟",
        "🦐",
        "🪼",
        "🦎",
        "🦖",
        "🦏",
        "🦍",
        "🦣",
        "🐫",
        "🐂",
        "🐕",
        "🦌",
        "🐎",
        "🫏",
    ]
    return random.choice(kind_emojis)


def save_data():
    with open(SUBSCRIPTIONS_FILE, "w") as f:
        json.dump({str(k): list(v) for k, v in user_subscriptions.items()}, f)
    with open(TOPICS_FILE, "w") as f:
        json.dump({str(k): list(v) for k, v in user_topics.items()}, f)


def load_data():
    global user_subscriptions, user_topics
    try:
        with open(SUBSCRIPTIONS_FILE, "r") as f:
            data = json.load(f)
            user_subscriptions = {int(k): set(v) for k, v in data.items()}
    except FileNotFoundError:
        user_subscriptions = {}
    try:
        with open(TOPICS_FILE, "r") as f:
            data = json.load(f)
            user_topics = {int(k): set(v) for k, v in data.items()}
    except FileNotFoundError:
        user_topics = {}


# Загружаем данные при запуске
load_data()

# Обработчики команд бота
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = set()
    if user_id not in user_topics:
        user_topics[user_id] = set()
    # Создаем меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_latest = types.KeyboardButton("Pull")
    btn_subscriptions = types.KeyboardButton("Мои подписки")
    btn_sources = types.KeyboardButton("Источники")
    #btn_topics = types.KeyboardButton("Темы")
    markup.add(btn_latest)
    markup.add(btn_subscriptions, btn_sources)
    #markup.add(btn_topics)
    bot.send_message(
        message.chat.id,
        "Здравствуйте! Вы можете использовать меню ниже для взаимодействия со мной.",
        reply_markup=markup,
    )


@bot.message_handler(func=lambda message: message.text == "Источники")
def list_sources(message):
    user_id = message.from_user.id
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = set()

    markup = types.InlineKeyboardMarkup()
    for source_key in RSS_SOURCES.keys():
        if source_key in user_subscriptions[user_id]:
            button = types.InlineKeyboardButton(
                text=f"Отписаться от {source_key}",
                callback_data=f"unsubscribe_{source_key}",
            )
        else:
            button = types.InlineKeyboardButton(
                text=f"Подписаться на {source_key}",
                callback_data=f"subscribe_{source_key}",
            )
        markup.add(button)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("subscribe_", "unsubscribe_"))
)
def callback_subscription(call):
    user_id = call.from_user.id
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = set()

    action, source_key = call.data.split("_", 1)

    if source_key not in RSS_SOURCES:
        bot.answer_callback_query(call.id, "Источник не найден.")
        return

    if action == "subscribe":
        user_subscriptions[user_id].add(source_key)
        bot.answer_callback_query(call.id, f"Вы подписались на {source_key}.")
    elif action == "unsubscribe":
        user_subscriptions[user_id].discard(source_key)
        bot.answer_callback_query(call.id, f"Вы отписались от {source_key}.")

    save_data()

    # Обновляем кнопки
    markup = types.InlineKeyboardMarkup()
    for key in RSS_SOURCES.keys():
        if key in user_subscriptions[user_id]:
            button = types.InlineKeyboardButton(
                text=f"Отписаться от {key}", callback_data=f"unsubscribe_{key}"
            )
        else:
            button = types.InlineKeyboardButton(
                text=f"Подписаться на {key}", callback_data=f"subscribe_{key}"
            )
        markup.add(button)
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )
    except Exception as e:
        print(f"Ошибка при обновлении клавиатуры: {e}")

@bot.message_handler(func=lambda message: message.text == "Мои подписки")
def list_subscriptions(message):
    user_id = message.from_user.id
    if user_id in user_subscriptions and user_subscriptions[user_id]:
        subscriptions = "\n".join([f"- {key}" for key in user_subscriptions[user_id]])
        bot.reply_to(message, f"Вы подписаны на следующие источники:\n{subscriptions}")
    else:
        bot.reply_to(message, "Вы не подписаны ни на один источник.")


#@bot.message_handler(func=lambda message: message.text == "Темы")
#def list_topics_menu(message):
#    user_id = message.from_user.id
#    if user_id not in user_topics:
#        user_topics[user_id] = set()
#
#    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#    btn_manage_topics = types.KeyboardButton("Управление темами")
#    btn_my_topics = types.KeyboardButton("Мои темы")
#    btn_back = types.KeyboardButton("Назад")
#    markup.add(btn_manage_topics)
#    markup.add(btn_my_topics)
#    markup.add(btn_back)
#    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


#@bot.message_handler(func=lambda message: message.text == "Управление темами")
#def manage_topics(message):
#    user_id = message.from_user.id
#    if user_id not in user_topics:
#        user_topics[user_id] = set()
#
#    markup = types.InlineKeyboardMarkup()
#    for topic in TOPICS:
#        if topic in user_topics[user_id]:
#            button = types.InlineKeyboardButton(
#                text=f"Отписаться от '{topic}'", callback_data=f"unsub_topic_{topic}"
#            )
#        else:
#            button = types.InlineKeyboardButton(
#                text=f"Подписаться на '{topic}'", callback_data=f"sub_topic_{topic}"
#            )
#        markup.add(button)
#    bot.send_message(
#        message.chat.id, "Выберите темы для подписки или отписки:", reply_markup=markup
#    )


#@bot.callback_query_handler(
#    func=lambda call: call.data.startswith(("sub_topic_", "unsub_topic_"))
#)
#def callback_topic_subscription(call):
#    user_id = call.from_user.id
#    if user_id not in user_topics:
#        user_topics[user_id] = set()
#
#    action, topic = call.data.split("_topic_", 1)
#
#    if topic not in TOPICS:
#        bot.answer_callback_query(call.id, "Тема не найдена.")
#        return
#
#    if action == "sub":
#        user_topics[user_id].add(topic)
#        bot.answer_callback_query(call.id, f"Вы подписались на тему '{topic}'.")
#    elif action == "unsub":
#        user_topics[user_id].discard(topic)
#        bot.answer_callback_query(call.id, f"Вы отписались от темы '{topic}'.")
#
#    save_data()
#
#    # Обновляем кнопки
#    markup = types.InlineKeyboardMarkup()
#    for t in TOPICS:
#        if t in user_topics[user_id]:
#            button = types.InlineKeyboardButton(
#                text=f"Отписаться от '{t}'", callback_data=f"unsub_topic_{t}"
#            )
#        else:
#            button = types.InlineKeyboardButton(
#                text=f"Подписаться на '{t}'", callback_data=f"sub_topic_{t}"
#            )
#        markup.add(button)
#    try:
#        bot.edit_message_reply_markup(
#            chat_id=call.message.chat.id,
#            message_id=call.message.message_id,
#            reply_markup=markup,
#        )
#    except Exception as e:
#        print(f"Ошибка при обновлении клавиатуры: {e}")

#@bot.message_handler(func=lambda message: message.text == "Мои темы")
#def show_my_topics(message):
#    user_id = message.from_user.id
#    if user_id in user_topics and user_topics[user_id]:
#        topics = "\n".join([f"- {topic}" for topic in user_topics[user_id]])
#        bot.reply_to(message, f"Вы подписаны на следующие темы:\n{topics}")
#    else:
#        bot.reply_to(message, "Вы не подписаны ни на одну тему.")


@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    # Возвращаем пользователя в главное меню
    send_welcome(message)

def send_article_list(chat_id, articles_mas: List[List[Article]], user_subscriptions):
    user_articles[chat_id] = []
    id_article = 0
    for theme_article, articles in zip(user_subscriptions, articles_mas):
        markup = types.InlineKeyboardMarkup()
        for _, article in enumerate(articles):
            button = types.InlineKeyboardButton(
                text=article.title[:50],  # Ограничиваем длину названия для кнопки
                callback_data=f'show_article_{id_article}'
            )
            markup.add(button)
            id_article+=1
        user_articles[chat_id].extend(articles)
        bot.send_message(chat_id, f"{theme_article}, Выберите статью для подробного просмотра:", reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == 'Pull')
def send_latest_articles(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in user_subscriptions or not user_subscriptions[user_id]:
        bot.reply_to(message, "Вы не подписаны ни на один источник. Используйте 'Источники', чтобы подписаться.")
        return
    articles = rss_processor.get_latest_articles(user_subscriptions[user_id], 10)

    if not articles:
        bot.reply_to(message, "Нет новых статей из ваших источников по выбранным темам.")
        return
    
    # Отправляем список статей с кнопками
    send_article_list(chat_id, articles, user_subscriptions[user_id])
    
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_article_'))
def callback_show_article(call):
    chat_id = call.message.chat.id
    idx = int(call.data[len('show_article_'):])

    if chat_id not in user_articles or idx >= len(user_articles[chat_id]):
        bot.answer_callback_query(call.id, "Статья не найдена.")
        return

    article = user_articles[chat_id][idx]
    
    prep_text = f"*{escape_markdown(article.title)}*\n" \
                   f"_Источник_: {escape_markdown(article.source)}\n" \
                   f"_Авторы_: {escape_markdown(article.authors)}\n" \
                   f"_Опубликовано_: {escape_markdown(article.published)}\n\n"
    message_text_AI = escape_markdown(
        model.invoke(
            f"Ты блогер-эксперт в области AI, тебе нужно простым языком по 5 пунктам сделать короткое и емкое описание о чем эта статья: {prep_text}, {article.summary}"
        ).content
    )      
     
    message_text = prep_text + message_text_AI
    
    message_text += f"\n\n [Ссылка на статью]({escape_markdown(article.link)})"
    if hasattr(article, 'pdf_link') and article.pdf_link:
        message_text += f" | [PDF]({escape_markdown(article.pdf_link)})"
    try:
        bot.send_message(chat_id, message_text, parse_mode='MarkdownV2', disable_web_page_preview=True)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при отправке статьи.")

        
@bot.message_handler(func=lambda message: message.chat.id == int(USER_CHAT_ID))
def handle_user_response(message):
    global PREPARE_PUB
    if PREPARE_PUB:
        if message.text.lower() in ["да"]:
            bot.send_message(CHANNEL_ID, PREPARE_PUB)
            PREPARE_PUB = None
            bot.send_message(USER_CHAT_ID, "Текст опубликован в канале.")
        else:
            bot.send_message(USER_CHAT_ID, "Публикация отменена.")


if __name__ == "__main__":
    thread = Thread(target=schedule_runner)
    thread.start()
    bot.polling(none_stop=True)

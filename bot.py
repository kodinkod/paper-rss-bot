import json
import time
from typing import Dict, Set
from rss_processors.feed_processor import (
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
    openai_api_key=os.environ.get("GPT"),
    base_url="https://api.proxyapi.ru/openai/v1",
)


RSS_SOURCES = {
    "HuggingFace Daily pappers": "https://jamesg.blog/hf-papers.xml",
    "arXiv AI": "https://arxiv.org/rss/cs.AI",
    "arXiv ML": "https://arxiv.org/rss/cs.LG",
    "arXiv Stat.ML": "https://arxiv.org/rss/stat.ML",
    "OpenAI Blog": "https://openai.com/blog/rss/",
}
TOPICS = ["NLP", "CV", "Generative Models"]

USER_CHAT_ID = 356509850
CHANNEL_ID = -1001569150954
TELEGRAM_TOKEN = os.environ.get("TG"),
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_subscriptions: Dict[int, Set[str]] = {}
PREPARE_PUB = None
PREPARE_PUB_PROMPT = "Напиши цитату из культовых мультфильмов или ситкомов c подписью: "


# Инициализация процессора RSS-ленты
rss_processor = RSSFeedProcessor()
rss_processor.register_feed("arXiv AI", RSS_SOURCES["arXiv AI"], ArxivRSSParser())
rss_processor.register_feed("arXiv ML", RSS_SOURCES["arXiv ML"], ArxivRSSParser())
rss_processor.register_feed(
    "arXiv Stat.ML", RSS_SOURCES["arXiv Stat.ML"], ArxivRSSParser()
)
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


@bot.message_handler(commands=["meme"])
def meme(message):
    anecdot = escape_markdown(model.invoke("Анекдот").content).replace("\.", ".")
    bot.send_message(message.chat.id, f"😁😁😁😁 Анекдот: {anecdot}")


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
    btn_latest = types.KeyboardButton("Последние статьи")
    btn_subscriptions = types.KeyboardButton("Мои подписки")
    btn_sources = types.KeyboardButton("Источники")
    btn_topics = types.KeyboardButton("Темы")
    markup.add(btn_latest)
    markup.add(btn_subscriptions, btn_sources)
    markup.add(btn_topics)
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


@bot.message_handler(func=lambda message: message.text == "Темы")
def list_topics_menu(message):
    user_id = message.from_user.id
    if user_id not in user_topics:
        user_topics[user_id] = set()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_manage_topics = types.KeyboardButton("Управление темами")
    btn_my_topics = types.KeyboardButton("Мои темы")
    btn_back = types.KeyboardButton("Назад")
    markup.add(btn_manage_topics)
    markup.add(btn_my_topics)
    markup.add(btn_back)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Управление темами")
def manage_topics(message):
    user_id = message.from_user.id
    if user_id not in user_topics:
        user_topics[user_id] = set()

    markup = types.InlineKeyboardMarkup()
    for topic in TOPICS:
        if topic in user_topics[user_id]:
            button = types.InlineKeyboardButton(
                text=f"Отписаться от '{topic}'", callback_data=f"unsub_topic_{topic}"
            )
        else:
            button = types.InlineKeyboardButton(
                text=f"Подписаться на '{topic}'", callback_data=f"sub_topic_{topic}"
            )
        markup.add(button)
    bot.send_message(
        message.chat.id, "Выберите темы для подписки или отписки:", reply_markup=markup
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("sub_topic_", "unsub_topic_"))
)
def callback_topic_subscription(call):
    user_id = call.from_user.id
    if user_id not in user_topics:
        user_topics[user_id] = set()

    action, topic = call.data.split("_topic_", 1)

    if topic not in TOPICS:
        bot.answer_callback_query(call.id, "Тема не найдена.")
        return

    if action == "sub":
        user_topics[user_id].add(topic)
        bot.answer_callback_query(call.id, f"Вы подписались на тему '{topic}'.")
    elif action == "unsub":
        user_topics[user_id].discard(topic)
        bot.answer_callback_query(call.id, f"Вы отписались от темы '{topic}'.")

    save_data()

    # Обновляем кнопки
    markup = types.InlineKeyboardMarkup()
    for t in TOPICS:
        if t in user_topics[user_id]:
            button = types.InlineKeyboardButton(
                text=f"Отписаться от '{t}'", callback_data=f"unsub_topic_{t}"
            )
        else:
            button = types.InlineKeyboardButton(
                text=f"Подписаться на '{t}'", callback_data=f"sub_topic_{t}"
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


@bot.message_handler(func=lambda message: message.text == "Мои темы")
def show_my_topics(message):
    user_id = message.from_user.id
    if user_id in user_topics and user_topics[user_id]:
        topics = "\n".join([f"- {topic}" for topic in user_topics[user_id]])
        bot.reply_to(message, f"Вы подписаны на следующие темы:\n{topics}")
    else:
        bot.reply_to(message, "Вы не подписаны ни на одну тему.")


@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    # Возвращаем пользователя в главное меню
    send_welcome(message)


@bot.message_handler(func=lambda message: message.text == "Последние статьи")
def send_latest_articles(message):
    user_id = message.from_user.id
    if user_id not in user_subscriptions or not user_subscriptions[user_id]:
        bot.reply_to(
            message,
            "Вы не подписаны ни на один источник. Используйте 'Источники', чтобы подписаться.",
        )
        return
    articles = rss_processor.get_latest_articles(user_subscriptions[user_id], 5)

    # Фильтруем статьи по темам
    if user_id in user_topics and user_topics[user_id]:
        topics = user_topics[user_id]
        filtered_articles = []
        for article in articles:
            article_text = f"{article.title} {article.summary}".lower()
            if any(topic.lower() in article_text for topic in topics):
                filtered_articles.append(article)
    else:
        filtered_articles = articles

    if not filtered_articles:
        bot.reply_to(
            message, "Нет новых статей из ваших источников по выбранным темам."
        )
        return

    for article in filtered_articles:
        AI_summary = escape_markdown(
            model.invoke(
                f"Please summarize the abstract of the scientific article in 5 short bullet points. Highlight the main ideas, results github links. Emphasize the key aspects to convey the essence of the research: {escape_markdown(article.summary)}  "
            ).content
        )
        emoji = get_random_kind_emoji()

        emoji_lang = escape_markdown(
            model.invoke(
                f"Translate this text into emoji language. Use 10 emojis.: {escape_markdown(article.summary)}  "
            ).content
        )

        message_text = (
            f"{emoji} *{escape_markdown(article.title)}*\n"
            f"_Авторы_: {escape_markdown(article.authors)}\n\n"
            f"{AI_summary} \n"
            f"_Опубликовано_: {escape_markdown(article.published)}\n\n"
            f"[Ссылка на статью]({escape_markdown(article.link)})\n\n"
            f"Язык эмоджи: {emoji_lang}"
        )

        if hasattr(article, "pdf_link") and article.pdf_link:
            message_text += f" | [PDF]({escape_markdown(article.pdf_link)})"
        if article.source:
            message_text += f"\n Источник: *{escape_markdown(article.source)}* \n"

        try:
            bot.send_message(
                message.chat.id,
                message_text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            time.sleep(0.5)
        
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

import feedparser
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from abc import ABC, abstractmethod

@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: str
    authors: str
    pdf_link: Optional[str] = None
    source: str = None

class BaseRSSParser(ABC):
    @abstractmethod
    def parse_feed(self, feed: feedparser.FeedParserDict) -> List[Article]:
        """Парсит RSS-ленту и возвращает список объектов Article."""
        pass

class ArxivRSSParser(BaseRSSParser):
    def parse_feed(self, feed: feedparser.FeedParserDict) -> List[Article]:
        articles: List[Article] = []
        for entry in feed.entries:
            try:
                title: str = entry.get('title', 'Без названия')
                link: str = entry.get('link', '')
                summary: str = entry.get('summary', '')
                published: str = entry.get('published', 'Неизвестно')
                authors_list = entry.get('authors', [])
                authors: str = ', '.join([author.name for author in authors_list]) if authors_list else 'Неизвестно'
                pdf_link: Optional[str] = next(
                    (l.href for l in entry.get('links', []) if l.type == 'application/pdf'), None
                )

                article = Article(
                    title=title,
                    link=link,
                    summary=summary,
                    published=published,
                    authors=authors,
                    pdf_link=pdf_link
                )
                articles.append(article)
            except Exception as e:
                print(f"Ошибка при парсинге записи: {e}")
        return articles

## Пример другого парсера для другого RSS-источника
class DailyHFRSSParser(BaseRSSParser):
    def parse_feed(self, feed: feedparser.FeedParserDict) -> List[Article]:
        # Реализуйте специфическую логику парсинга для другого источника
        articles: List[Article] = []
        for entry in feed.entries:
            # Пример парсинга, замените на актуальные поля
            title: str = entry.get('title', 'Без названия')
            link: str = entry.get('link', '')
            summary: str = entry.get('description', '')
            published: str = entry.get('pubDate', 'Неизвестно')
            authors: str = entry.get('author', 'Неизвестно')
            
            article = Article(
                title=title,
                link=link,
                summary=summary,
                published=published,
                authors=authors,
                source="Daily papers"
            )
            articles.append(article)
        return articles


class RSSFeedFetcher:
    def __init__(self, feed_url: str):
        self.feed_url = feed_url

    def fetch_feed(self) -> feedparser.FeedParserDict:
        """Загружает и парсит RSS-ленту."""
        try:
            feed = feedparser.parse(self.feed_url)
            if feed.bozo:
                raise ValueError(f"Ошибка при парсинге RSS-ленты: {feed.bozo_exception}")
            return feed
        except Exception as e:
            print(f"Ошибка при загрузке ленты: {e}")
            return feedparser.FeedParserDict()

class RSSFeedProcessor:
    def __init__(self):
        self.feed_parsers: Dict[str, BaseRSSParser] = {}
        self.feed_urls: Dict[str, str] = {}

    def register_feed(self, source_key: str, feed_url: str, parser: BaseRSSParser):
        self.feed_parsers[source_key] = parser
        self.feed_urls[source_key] = feed_url

    def get_latest_articles(self, sources: Set[str], count: int = 1) -> List[Article]:
        all_articles: List[Article] = []
        for source_key in sources:
            parser = self.feed_parsers.get(source_key)
            feed_url = self.feed_urls.get(source_key)
            if parser and feed_url:
                fetcher = RSSFeedFetcher(feed_url)
                feed = fetcher.fetch_feed()
                articles = parser.parse_feed(feed)
                all_articles.extend(articles[:count])
            else:
                print(f"Источник {source_key} не найден или не имеет парсера")
        # Сортировка статей по дате публикации (опционально)
        all_articles.sort(key=lambda x: x.published, reverse=True)
        return all_articles[:count*len(sources)]
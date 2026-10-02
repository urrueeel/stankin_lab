"""
Лабораторная работа № 1. ООП в Python. Обработка исключительных ситуаций.
Форматы XML и JSON.

Вариант: предметная область «книжная библиотека».
Классы: Book (книга) и Magazine (журнал), общий базовый класс Publication.

Хранение:
  - объекты класса Book     -> формат JSON
  - объекты класса Magazine -> формат XML

Пункты работы:
  2) диаграмма классов UML  -> diagram.drawio
  3) код на Python по диаграмме классов
  4) обработка встроенных и собственных исключений
  5) структура данных в XML и JSON (файлы data_books.json, data_magazines.xml)
  6) считывание из файла и запись в файл XML (ElementTree) и JSON (json)
"""

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


# =========================================================================
# 4) Собственные исключения (иерархия от базового PublicationError)
# =========================================================================
class PublicationError(Exception):
    """Базовое собственное исключение для предметной области."""


class EmptyTitleError(PublicationError):
    """Название издания не может быть пустым."""


class InvalidYearError(PublicationError):
    """Год издания вне допустимого диапазона."""


class InvalidIsbnError(PublicationError):
    """Некорректный формат ISBN."""


class DataFormatError(PublicationError):
    """Ошибка формата данных при чтении/записи файла."""


# =========================================================================
# 3) Базовый абстрактный класс Publication
# =========================================================================
class Publication(ABC):
    """Абстрактное издание: общие поля книги и журнала."""

    def __init__(self, title: str, year: int, publisher: str) -> None:
        # Встроенное исключение ValueError при пустом названии
        if not title or not title.strip():
            raise EmptyTitleError("Название издания не может быть пустым")
        # Собственное исключение при некорректном годе
        if not (1450 <= year <= 2100):
            raise InvalidYearError(
                f"Год издания {year} вне допустимого диапазона [1450, 2100]"
            )
        self.title = title.strip()
        self.year = year
        self.publisher = publisher

    @abstractmethod
    def get_info(self) -> str:
        """Абстрактный метод: краткая информация об издании."""

    def __str__(self) -> str:
        return self.get_info()


# =========================================================================
# 3) Класс Book (хранится в JSON)
# =========================================================================
class Book(Publication):
    """Книга. Наследует Publication, добавляет ISBN, автора и число страниц."""

    def __init__(self, title: str, author: str, year: int,
                 publisher: str, isbn: str, pages: int) -> None:
        super().__init__(title, year, publisher)
        # Собственное исключение при некорректном ISBN
        if not isbn or len(isbn.replace("-", "")) not in (10, 13):
            raise InvalidIsbnError(f"Некорректный ISBN: {isbn!r}")
        if pages <= 0:
            # Встроенное исключение ValueError
            raise ValueError(f"Число страниц должно быть положительным, получено {pages}")
        self.author = author
        self.isbn = isbn
        self.pages = pages

    def get_info(self) -> str:
        return (f"Книга: «{self.title}» — {self.author}, "
                f"{self.year}, {self.publisher}, ISBN {self.isbn}, {self.pages} стр.")

    # --- сериализация в JSON (пункт 6) ---
    def to_dict(self) -> dict:
        """Преобразование объекта в словарь для JSON."""
        return {
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "publisher": self.publisher,
            "isbn": self.isbn,
            "pages": self.pages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """Создание объекта из словаря (десериализация JSON)."""
        try:
            return cls(
                title=data["title"],
                author=data["author"],
                year=int(data["year"]),
                publisher=data["publisher"],
                isbn=data["isbn"],
                pages=int(data["pages"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataFormatError(f"Некорректные данные книги: {exc}") from exc


# =========================================================================
# 3) Класс Magazine (хранится в XML)
# =========================================================================
class Magazine(Publication):
    """Журнал. Наследует Publication, добавляет номер выпуска и периодичность."""

    def __init__(self, title: str, year: int, publisher: str,
                 issue_number: int, periodicity: str) -> None:
        super().__init__(title, year, publisher)
        if issue_number <= 0:
            raise ValueError(f"Номер выпуска должен быть положительным, получено {issue_number}")
        self.issue_number = issue_number
        self.periodicity = periodicity

    def get_info(self) -> str:
        return (f"Журнал: «{self.title}» — выпуск №{self.issue_number}, "
                f"{self.year}, {self.publisher}, периодичность: {self.periodicity}")

    # --- сериализация в XML (пункт 6) ---
    def to_xml(self) -> ET.Element:
        """Преобразование объекта в XML-элемент."""
        elem = ET.Element("magazine")
        ET.SubElement(elem, "title").text = self.title
        ET.SubElement(elem, "year").text = str(self.year)
        ET.SubElement(elem, "publisher").text = self.publisher
        ET.SubElement(elem, "issue_number").text = str(self.issue_number)
        ET.SubElement(elem, "periodicity").text = self.periodicity
        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> "Magazine":
        """Создание объекта из XML-элемента (десериализация)."""
        try:
            return cls(
                title=element.findtext("title", ""),
                year=int(element.findtext("year", "0")),
                publisher=element.findtext("publisher", ""),
                issue_number=int(element.findtext("issue_number", "0")),
                periodicity=element.findtext("periodicity", ""),
            )
        except (TypeError, ValueError) as exc:
            raise DataFormatError(f"Некорректные данные журнала: {exc}") from exc


# =========================================================================
# 3) Класс Library — хранилище и работа с файлами
# =========================================================================
class Library:
    """Библиотека: коллекции книг и журналов, чтение/запись файлов."""

    def __init__(self) -> None:
        self.books: list[Book] = []
        self.magazines: list[Magazine] = []

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def add_magazine(self, magazine: Magazine) -> None:
        self.magazines.append(magazine)

    # --- JSON: книги (пункт 6) ---
    def save_books_json(self, path: str) -> None:
        """Запись списка книг в JSON-файл."""
        data = [book.to_dict() for book in self.books]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать файл {path}: {exc}") from exc

    def load_books_json(self, path: str) -> None:
        """Чтение списка книг из JSON-файла."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise DataFormatError(f"Не удалось прочитать файл {path}: {exc}") from exc
        if not isinstance(data, list):
            raise DataFormatError(f"Ожидался список книг в файле {path}")
        self.books = [Book.from_dict(item) for item in data]

    # --- XML: журналы (пункт 6) ---
    def save_magazines_xml(self, path: str) -> None:
        """Запись списка журналов в XML-файл (модуль ElementTree)."""
        root = ET.Element("magazines")
        for magazine in self.magazines:
            root.append(magazine.to_xml())
        tree = ET.ElementTree(root)
        try:
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать файл {path}: {exc}") from exc

    def load_magazines_xml(self, path: str) -> None:
        """Чтение списка журналов из XML-файла."""
        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            raise DataFormatError(f"Не удалось прочитать файл {path}: {exc}") from exc
        root = tree.getroot()
        if root.tag != "magazines":
            raise DataFormatError(f"Корневой элемент должен быть <magazines>, найден <{root.tag}>")
        self.magazines = [Magazine.from_xml(elem) for elem in root.findall("magazine")]

    def show_all(self) -> None:
        """Вывод всех изданий на экран."""
        print("=" * 60)
        print("КНИГИ (JSON):")
        for book in self.books:
            print("  -", book)
        print("ЖУРНАЛЫ (XML):")
        for magazine in self.magazines:
            print("  -", magazine)
        print("=" * 60)


# =========================================================================
# 4) Демонстрация обработки исключений
# =========================================================================
def demo_exceptions() -> None:
    """Проверка встроенных и собственных исключений."""
    print("\n--- Демонстрация обработки исключений ---")

    # Собственное исключение: пустое название
    try:
        Book("", "Иванов", 2020, "Питер", "978-5-00000-000-0", 100)
    except EmptyTitleError as exc:
        print(f"[EmptyTitleError] {exc}")

    # Собственное исключение: некорректный год
    try:
        Magazine("Наука", 1300, "Мир", 1, "ежемесячно")
    except InvalidYearError as exc:
        print(f"[InvalidYearError] {exc}")

    # Собственное исключение: некорректный ISBN
    try:
        Book("Python", "Петров", 2021, "Питер", "123", 200)
    except InvalidIsbnError as exc:
        print(f"[InvalidIsbnError] {exc}")

    # Встроенное исключение: отрицательное число страниц
    try:
        Book("Python", "Петров", 2021, "Питер", "978-5-00000-000-0", -5)
    except ValueError as exc:
        print(f"[ValueError] {exc}")

    # Встроенное исключение: деление на ноль (ZeroDivisionError)
    try:
        pages = 0
        ratio = 100 / pages
    except ZeroDivisionError as exc:
        print(f"[ZeroDivisionError] {exc}")

    # Собственное исключение: ошибка формата данных
    try:
        Book.from_dict({"title": "Без полей"})
    except DataFormatError as exc:
        print(f"[DataFormatError] {exc}")

    # Обработка нескольких исключений в одном блоке
    try:
        with open("no_such_file.json", "r", encoding="utf-8") as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[FileNotFoundError/JSONDecodeError] {exc}")

    # Блок else / finally
    try:
        value = int("42")
    except ValueError:
        print("Не число")
    else:
        print(f"[else] Преобразование успешно: {value}")
    finally:
        print("[finally] Блок finally выполняется всегда")


# =========================================================================
# 5) Создание файлов данных (структура + данные нескольких объектов)
# =========================================================================
def create_data_files() -> None:
    """Формирует data_books.json и data_magazines.xml с данными объектов."""
    lib = Library()
    lib.add_book(Book("Война и мир", "Л. Н. Толстой", 1869,
                      "Эксмо", "978-5-04-000000-1", 1300))
    lib.add_book(Book("Преступление и наказание", "Ф. М. Достоевский", 1866,
                      "АСТ", "978-5-17-000000-2", 672))
    lib.add_book(Book("Мастер и Маргарита", "М. А. Булгаков", 1967,
                      "Азбука", "978-5-389-00000-3", 480))

    lib.add_magazine(Magazine("Наука и жизнь", 2023, "Наука", 1, "ежемесячно"))
    lib.add_magazine(Magazine("Вокруг света", 2022, "Вокруг света", 12, "ежемесячно"))
    lib.add_magazine(Magazine("Квант", 2021, "МЦНМО", 4, "ежеквартально"))

    lib.save_books_json("data_books.json")
    lib.save_magazines_xml("data_magazines.xml")
    print("Созданы файлы: data_books.json, data_magazines.xml")


# =========================================================================
# 6) Чтение данных из файлов
# =========================================================================
def read_data_files() -> Library:
    """Читает книги из JSON и журналы из XML, возвращает Library."""
    lib = Library()
    lib.load_books_json("data_books.json")
    lib.load_magazines_xml("data_magazines.xml")
    return lib


# =========================================================================
# Точка входа
# =========================================================================
def main() -> None:
    # Пункт 4: демонстрация исключений
    demo_exceptions()

    # Пункт 5: создание файлов данных
    create_data_files()

    # Пункт 6: чтение из файлов и вывод
    print("\n--- Чтение данных из файлов ---")
    lib = read_data_files()
    lib.show_all()


if __name__ == "__main__":
    main()
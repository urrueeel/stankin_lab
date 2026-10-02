"""
Лабораторная работа № 1. ООП в Python. Обработка исключительных ситуаций.
Форматы XML и JSON.

Вариант 15: предметная область «домашние животные».
Классы: Dog (собака) и Cat (кошка), общий базовый класс Pet.

Хранение:
  - объекты класса Dog -> формат JSON
  - объекты класса Cat -> формат XML

Пункты работы:
  3) код на Python по диаграмме классов
  4) обработка встроенных и собственных исключений
  5) структура данных в XML и JSON
  6) считывание из файла и запись в файл XML (ElementTree) и JSON (json)
"""

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


# =========================================================================
# 4) Собственные исключения (иерархия от базового PetError)
# =========================================================================
class PetError(Exception):
    """Базовое собственное исключение для предметной области домашних животных."""


class EmptyNameError(PetError):
    """Имя животного не может быть пустым."""


class InvalidAgeError(PetError):
    """Возраст животного вне допустимого диапазона."""


class InvalidWeightError(PetError):
    """Некорректный вес животного."""


class DataFormatError(PetError):
    """Ошибка формата данных при чтении/записи файла."""


# =========================================================================
# 3) Базовый абстрактный класс Pet
# =========================================================================
class Pet(ABC):
    """Абстрактное домашнее животное с общими характеристиками."""

    def __init__(self, name: str, age: int, weight: float, owner: str) -> None:
        if not name or not name.strip():
            raise EmptyNameError("Имя животного не может быть пустым")
        if not (0 <= age <= 100):
            raise InvalidAgeError(
                f"Возраст животного {age} вне допустимого диапазона [0, 100]"
            )
        if weight <= 0:
            raise InvalidWeightError(f"Вес должен быть положительным, получено {weight}")
        self.name = name.strip()
        self.age = age
        self.weight = weight
        self.owner = owner.strip() if owner else "Не указан"

    @abstractmethod
    def get_info(self) -> str:
        """Абстрактный метод: краткая информация о животном."""

    def __str__(self) -> str:
        return self.get_info()


# =========================================================================
# 3) Класс Dog (хранится в JSON)
# =========================================================================
class Dog(Pet):
    """Собака. Добавляет породу и информацию о дрессировке."""

    def __init__(self, name: str, age: int, weight: float, owner: str,
                 breed: str, trained: bool) -> None:
        super().__init__(name, age, weight, owner)
        if not breed or not breed.strip():
            raise ValueError("Порода собаки не может быть пустой")
        self.breed = breed.strip()
        self.trained = bool(trained)

    def get_info(self) -> str:
        training = "дрессирована" if self.trained else "не дрессирована"
        return (f"Собака: {self.name}, порода: {self.breed}, возраст: {self.age} лет, "
                f"вес: {self.weight} кг, хозяин: {self.owner}, {training}")

    # --- сериализация в JSON (пункт 6) ---
    def to_dict(self) -> dict:
        """Преобразование объекта в словарь для JSON."""
        return {
            "name": self.name,
            "age": self.age,
            "weight": self.weight,
            "owner": self.owner,
            "breed": self.breed,
            "trained": self.trained,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Dog":
        """Создание объекта из словаря (десериализация JSON)."""
        try:
            return cls(
                name=data["name"],
                age=int(data["age"]),
                weight=float(data["weight"]),
                owner=data["owner"],
                breed=data["breed"],
                trained=data["trained"],
            )
        except (KeyError, TypeError, ValueError, PetError) as exc:
            raise DataFormatError(f"Некорректные данные собаки: {exc}") from exc


# =========================================================================
# 3) Класс Cat (хранится в XML)
# =========================================================================
class Cat(Pet):
    """Кошка. Добавляет породу и любимую игрушку."""

    def __init__(self, name: str, age: int, weight: float, owner: str,
                 breed: str, favorite_toy: str) -> None:
        super().__init__(name, age, weight, owner)
        if not breed or not breed.strip():
            raise ValueError("Порода кошки не может быть пустой")
        self.breed = breed.strip()
        self.favorite_toy = favorite_toy.strip() if favorite_toy else "Не указана"

    def get_info(self) -> str:
        return (f"Кошка: {self.name}, порода: {self.breed}, возраст: {self.age} лет, "
                f"вес: {self.weight} кг, хозяин: {self.owner}, "
                f"любимая игрушка: {self.favorite_toy}")

    # --- сериализация в XML (пункт 6) ---
    def to_xml(self) -> ET.Element:
        """Преобразование объекта в XML-элемент."""
        elem = ET.Element("cat")
        ET.SubElement(elem, "name").text = self.name
        ET.SubElement(elem, "age").text = str(self.age)
        ET.SubElement(elem, "weight").text = str(self.weight)
        ET.SubElement(elem, "owner").text = self.owner
        ET.SubElement(elem, "breed").text = self.breed
        ET.SubElement(elem, "favorite_toy").text = self.favorite_toy
        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> "Cat":
        """Создание объекта из XML-элемента (десериализация)."""
        try:
            return cls(
                name=element.findtext("name", ""),
                age=int(element.findtext("age", "0")),
                weight=float(element.findtext("weight", "0")),
                owner=element.findtext("owner", ""),
                breed=element.findtext("breed", ""),
                favorite_toy=element.findtext("favorite_toy", ""),
            )
        except (TypeError, ValueError, PetError) as exc:
            raise DataFormatError(f"Некорректные данные кошки: {exc}") from exc


# =========================================================================
# 3) Класс PetShelter — хранилище и работа с файлами
# =========================================================================
class PetShelter:
    """Домашние животные: коллекции собак и кошек, чтение/запись файлов."""

    def __init__(self) -> None:
        self.dogs: list[Dog] = []
        self.cats: list[Cat] = []

    def add_dog(self, dog: Dog) -> None:
        self.dogs.append(dog)

    def add_cat(self, cat: Cat) -> None:
        self.cats.append(cat)

    # --- JSON: собаки (пункт 6) ---
    def save_dogs_json(self, path: str) -> None:
        """Запись списка собак в JSON-файл."""
        data = [dog.to_dict() for dog in self.dogs]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать файл {path}: {exc}") from exc

    def load_dogs_json(self, path: str) -> None:
        """Чтение списка собак из JSON-файла."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise DataFormatError(f"Не удалось прочитать файл {path}: {exc}") from exc
        if not isinstance(data, list):
            raise DataFormatError(f"Ожидался список собак в файле {path}")
        self.dogs = [Dog.from_dict(item) for item in data]

    # --- XML: кошки (пункт 6) ---
    def save_cats_xml(self, path: str) -> None:
        """Запись списка кошек в XML-файл (модуль ElementTree)."""
        root = ET.Element("cats")
        for cat in self.cats:
            root.append(cat.to_xml())
        tree = ET.ElementTree(root)
        try:
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать файл {path}: {exc}") from exc

    def load_cats_xml(self, path: str) -> None:
        """Чтение списка кошек из XML-файла."""
        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            raise DataFormatError(f"Не удалось прочитать файл {path}: {exc}") from exc
        root = tree.getroot()
        if root.tag != "cats":
            raise DataFormatError(
                f"Корневой элемент должен быть <cats>, найден <{root.tag}>"
            )
        self.cats = [Cat.from_xml(elem) for elem in root.findall("cat")]

    def show_all(self) -> None:
        """Вывод всех домашних животных на экран."""
        print("=" * 60)
        print("СОБАКИ (JSON):")
        for dog in self.dogs:
            print("  -", dog)
        print("КОШКИ (XML):")
        for cat in self.cats:
            print("  -", cat)
        print("=" * 60)


# =========================================================================
# 4) Демонстрация обработки исключений
# =========================================================================
def demo_exceptions() -> None:
    """Проверка встроенных и собственных исключений."""
    print("\n--- Демонстрация обработки исключений ---")

    # Собственное исключение: пустое имя
    try:
        Dog("", 3, 12.5, "Иван", "Лабрадор", True)
    except EmptyNameError as exc:
        print(f"[EmptyNameError] {exc}")

    # Собственное исключение: некорректный возраст
    try:
        Cat("Мурка", -2, 4.0, "Анна", "Британская", "Мячик")
    except InvalidAgeError as exc:
        print(f"[InvalidAgeError] {exc}")

    # Собственное исключение: некорректный вес
    try:
        Dog("Бобик", 5, -1, "Иван", "Дворняга", False)
    except InvalidWeightError as exc:
        print(f"[InvalidWeightError] {exc}")

    # Встроенное исключение: пустая порода
    try:
        Cat("Мурка", 2, 3.5, "Анна", "", "Мячик")
    except ValueError as exc:
        print(f"[ValueError] {exc}")

    # Встроенное исключение: деление на ноль (ZeroDivisionError)
    try:
        animals = 0
        ratio = 100 / animals
    except ZeroDivisionError as exc:
        print(f"[ZeroDivisionError] {exc}")

    # Собственное исключение: ошибка формата данных
    try:
        Dog.from_dict({"name": "Без полей"})
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
    """Формирует data_dogs.json и data_cats.xml с данными объектов."""
    shelter = PetShelter()
    shelter.add_dog(Dog("Бобик", 5, 12.5, "Иван Петров", "Лабрадор", True))
    shelter.add_dog(Dog("Рекс", 3, 18.0, "Мария Иванова", "Овчарка", True))
    shelter.add_dog(Dog("Тузик", 7, 9.2, "Алексей Смирнов", "Дворняга", False))

    shelter.add_cat(Cat("Мурка", 2, 3.5, "Анна Иванова", "Британская", "Мячик"))
    shelter.add_cat(Cat("Барсик", 4, 5.1, "Павел Сидоров", "Сибирская", "Мышка"))
    shelter.add_cat(Cat("Луна", 1, 2.8, "Елена Кузнецова", "Сиамская", "Верёвочка"))

    shelter.save_dogs_json("data_dogs.json")
    shelter.save_cats_xml("data_cats.xml")
    print("Созданы файлы: data_dogs.json, data_cats.xml")


# =========================================================================
# 6) Чтение данных из файлов
# =========================================================================
def read_data_files() -> PetShelter:
    """Читает собак из JSON и кошек из XML, возвращает PetShelter."""
    shelter = PetShelter()
    shelter.load_dogs_json("data_dogs.json")
    shelter.load_cats_xml("data_cats.xml")
    return shelter


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
    shelter = read_data_files()
    shelter.show_all()


if __name__ == "__main__":
    main()

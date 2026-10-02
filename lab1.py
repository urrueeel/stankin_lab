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



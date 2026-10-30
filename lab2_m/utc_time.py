import re
from pathlib import Path
from urllib.request import Request, urlopen

# Диапазоны часов, минут и секунд и обязательное обозначение UTC.
BODY = r'(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:Z| UTC)'
TIME = re.compile(BODY)
SEARCH = re.compile(r'(?<![\w:])' + BODY + r'(?![\w:])')


def is_utc_time(value):
    return TIME.fullmatch(value) is not None


def find_utc_times(text):
    return [match.group() for match in SEARCH.finditer(text)]


def read_page(url):
    if not url.startswith(('http://', 'https://')):
        raise ValueError('URL должен начинаться с http:// или https://')
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(request, timeout=10) as response:
        encoding = response.headers.get_content_charset() or 'utf-8'
        return response.read().decode(encoding, errors='replace')


def main():
    print('Проверка и поиск времени UTC')
    print('Формат: ЧЧ:ММ:ССZ или ЧЧ:ММ:СС UTC')
    print('1 — проверить ввод; 2 — поиск в файле; 3 — поиск по URL')
    choice = input('Выберите режим: ').strip()
    try:
        if choice == '1':
            value = input('Введите время: ').strip()
            print('Корректное время UTC' if is_utc_time(value)
                  else 'Некорректное время UTC')
            return
        if choice == '2':
            path = Path(input('Путь к файлу UTF-8: ').strip())
            text = path.read_text(encoding='utf-8-sig')
        elif choice == '3':
            text = read_page(input('URL страницы: ').strip())
        else:
            print('Неизвестный режим')
            return
        matches = find_utc_times(text)
        if matches:
            print(f'Найдено: {len(matches)}')
            for item in matches:
                print(item)
        else:
            print('Совпадений не найдено')
    except (OSError, UnicodeError, ValueError, LookupError) as error:
        print(f'Ошибка чтения: {error}')


if __name__ == '__main__':
    main()

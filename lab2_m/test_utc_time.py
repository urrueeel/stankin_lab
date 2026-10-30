import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError

from utc_time import find_utc_times, is_utc_time, main, read_page


class TimeTests(unittest.TestCase):
    def test_valid(self):
        for value in ('00:00:00Z', '23:59:59 UTC', '12:34:56Z'):
            with self.subTest(value=value):
                self.assertTrue(is_utc_time(value))

    def test_invalid(self):
        for value in ('24:00:00Z', '12:60:00Z', '12:00:60 UTC',
                      '1:02:03Z', '12:00Z', '12:00:00', '12:00:00z',
                      '12:00:00+00:00', '12:00:00Z!', '', '１２:００:００Z'):
            with self.subTest(value=value):
                self.assertFalse(is_utc_time(value))

    def test_search(self):
        self.assertEqual(find_utc_times('00:00:00Z, 23:59:59 UTC; 00:00:00Z'),
                         ['00:00:00Z', '23:59:59 UTC', '00:00:00Z'])

    def test_boundaries(self):
        self.assertEqual(find_utc_times('x12:00:00Z 112:00:00Z 12:00:00Zx '
                                        '12:00:00Z:4 24:00:00Z'), [])

    def test_empty(self):
        self.assertEqual(find_utc_times('нет времени'), [])


class PageTests(unittest.TestCase):
    @patch('utc_time.urlopen')
    def test_page(self, mock_open):
        response = mock_open.return_value.__enter__.return_value
        response.headers.get_content_charset.return_value = 'utf-8'
        response.read.return_value = 'Время 12:30:00Z'.encode()
        self.assertEqual(read_page('https://example.com'), 'Время 12:30:00Z')
        self.assertEqual(mock_open.call_args.kwargs['timeout'], 10)

    def test_scheme(self):
        with self.assertRaises(ValueError):
            read_page('file:///example')

    @patch('utc_time.urlopen', side_effect=URLError('network'))
    def test_error(self, mock_open):
        with self.assertRaises(URLError):
            read_page('https://example.com')


class MenuTests(unittest.TestCase):
    def run_menu(self, values):
        output = io.StringIO()
        with patch('builtins.input', side_effect=values), redirect_stdout(output):
            main()
        return output.getvalue()

    def test_validation(self):
        self.assertIn('Корректное время UTC', self.run_menu(['1', '12:00:00Z']))
        self.assertIn('Некорректное время UTC', self.run_menu(['1', '25:00:00Z']))

    @patch('utc_time.Path.read_text', return_value='Время: 12:00:00Z')
    def test_file(self, mock_read):
        self.assertIn('12:00:00Z', self.run_menu(['2', 'example.txt']))
        mock_read.assert_called_once_with(encoding='utf-8-sig')

    @patch('utc_time.read_page', return_value='Нет записей')
    def test_url(self, mock_read):
        self.assertIn('Совпадений не найдено', self.run_menu(['3', 'https://example.com']))

    def test_errors(self):
        self.assertIn('Неизвестный режим', self.run_menu(['4']))
        self.assertIn('Ошибка чтения', self.run_menu(['2', 'missing-file.txt']))


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch
from io import StringIO
from src.handler.command_handler import CommandHandler
from src.handler.chat_handler import ChatHandler

class TestCLIFunctionality(unittest.TestCase):
    def setUp(self):
        self.chat_handler = ChatHandler()
        self.command_handler = CommandHandler(chat_handler=self.chat_handler)

    def test_quit_command(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = self.command_handler.handle_command('/quit')
            self.assertFalse(result)
            self.assertIn('退出', fake_out.getvalue())

    def test_multi_command_handling(self):
        self.command_handler.handle_command('/multi')
        self.assertTrue(self.chat_handler.multi_mode)

    @patch('builtins.input', side_effect=['line1', 'line2', '/eof'])
    def test_multi_line_input(self, mock_input):
        self.chat_handler.multi_mode = True
        lines = []
        while True:
            line = input('> ')
            if line == '/eof':
                break
            lines.append(line)
        self.assertEqual(len(lines), 2)

if __name__ == '__main__':
    unittest.main()
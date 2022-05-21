import random
import re
from collections import defaultdict
from typing import List


class FindAnswer:
    def __init__(self, n_letters=5) -> None:
        self._number_of_letters = n_letters
        self._all_letters = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
        self._current_state = 0
        self._current_regular_expression = [self._all_letters] * self._number_of_letters
        self._known_letters = defaultdict(
            int
        )  # letters that should be in a secret word
        self._all_words = []
        self._current_available_words = []  # current pool of words

        self._previous_words_states = []
        self._previous_words = []  # words that have been entered
        self._load_words()

    def reset(self):
        self._previous_words.clear()
        self._previous_words_states.clear()
        self._known_letters.clear()
        self._current_available_words = self._all_words.copy()
        self._current_regular_expression = [self._all_letters] * self._number_of_letters
        self._current_state = 0

    def get_random_word(self):
        if self._current_state == 0:
            return 'клише'
        elif self._current_state == 1:
            return 'загон'
        return random.choice(self._all_words)

    def _preprocessing_text(self, lines: List[str]):
        new_lines = [word.strip() for word in lines]
        new_lines = [word.lower() for word in new_lines if word.isalpha()]
        new_lines = [word for word in new_lines if len(word) == self._number_of_letters]
        new_lines = [word.replace("ё", "е") for word in new_lines]
        new_lines = list(set(new_lines))
        return new_lines

    def _load_words(self, filename="rus_words_no_duplicates.txt"):
        with open(filename, "r") as f:
            new_lines = f.readlines()
        # new_lines = [word.decode("WINDOWS-1251") for word in lines]
        self._all_words = self._preprocessing_text(new_lines)
        self._current_available_words = self._all_words.copy()

    def _apply_regular(self):
        pattern = f"[{']['.join(self._current_regular_expression)}]"
        prog = re.compile(pattern)
        regular_list = [
            word for word in self._current_available_words if prog.search(word)
        ]
        RESULT_LIST = []
        for word in regular_list:
            flag = True
            for letter in self._known_letters:
                if not letter in word:
                    flag = False
            if flag:
                RESULT_LIST.append(word)
        self._current_available_words = RESULT_LIST

    def _remove_letter_from_regular(self, letter, position=None):
        if not letter in self._known_letters:
            for i in range(self._number_of_letters):
                self._current_regular_expression[i] = self._current_regular_expression[
                    i
                ].replace(letter, "")
        else:
            self._current_regular_expression[
                position
            ] = self._current_regular_expression[position].replace(letter, "")

    def get_next_word(self):
        if len(self._current_available_words) == 0:
            raise Exception("No words more")
        return random.choice(self._current_available_words)

    def response_from_game(self, word=None, state_of_word=None):
        assert len(word) == len(state_of_word) == self._number_of_letters
        # - : now such letter
        # * : letter not in its position
        # + : letter in its position

        self._previous_words.append(word)
        self._previous_words_states.append(state_of_word)
        for i, letter, state_of_letter in zip(range(len(word)), word, state_of_word):
            if state_of_letter == "-":
                self._remove_letter_from_regular(letter, i)
            elif state_of_letter == "+":
                self._known_letters[letter] += 1
                self._current_regular_expression[i] = letter
            elif state_of_letter == "*":
                self._known_letters[letter] += 1
                self._current_regular_expression[i] = self._current_regular_expression[
                    i
                ].replace(letter, "")
            else:
                raise Exception("Wrong state")
        
        self._current_state += 1

        self._apply_regular()

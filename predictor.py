import random
import re
from collections import defaultdict
from pathlib import Path
from typing import List

import numpy as np


class FindAnswer:
    def __init__(self, n_letters=5) -> None:
        self._number_of_letters = n_letters
        self._all_letters = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
        self._current_state = 0
        self._current_regular_expression = [self._all_letters] * self._number_of_letters
        self._known_letters = defaultdict(
            int
        )  # letters that should be in a secret word
        self._max_letter_counts = {}
        self._all_words = []
        self._current_available_words = []  # current pool of words

        self._previous_words_states = []
        self._previous_words = []  # words that have been entered
        self._load_words()

        # self._letter_probabilites = None
        self._current_available_words_with_probs = defaultdict(float)

        self._count_probs_call = 0

    def reset(self):
        self._previous_words.clear()
        self._previous_words_states.clear()
        self._known_letters.clear()
        self._max_letter_counts.clear()
        self._current_available_words = self._all_words.copy()
        self._current_regular_expression = [self._all_letters] * self._number_of_letters
        self._current_state = 0
        self._current_available_words_with_probs.clear()
        self._count_probs_call = 0

    def _count_probs(self):
        self._current_available_words_with_probs = defaultdict(float)
        self._count_probs_call += 1
        letter_index = {letter: index for index, letter in enumerate(self._all_letters)}
        letter_counts = np.zeros((len(self._all_letters), self._number_of_letters))
        for word in self._current_available_words:
            for index, letter in enumerate(word):
                letter_counts[letter_index[letter]][index] += 1

        letter_probabilites = letter_counts / letter_counts.T.sum(1)
        for word in self._current_available_words:
            prob = 1.0
            for index, letter in enumerate(word):
                prob *= letter_probabilites[letter_index[letter]][index]
            self._current_available_words_with_probs[word] = prob

    def get_clever_random_word(self):
        """Count probabilites of letters"""
        if self._count_probs_call <= self._current_state:
            self._count_probs()

        return random.choices(
            list(self._current_available_words_with_probs.keys()),
            weights=self._current_available_words_with_probs.values(),
            k=1,
        )[0]

    def get_random_word(self):
        # if self._current_state == 0:
        #     return "клише"
        # elif self._current_state == 1:
        #     return "загон"
        return random.choice(self._all_words)

    def _preprocessing_text(self, lines: List[str]):
        new_lines = [word.strip() for word in lines]
        new_lines = [word.lower() for word in new_lines if word.isalpha()]
        new_lines = [word for word in new_lines if len(word) == self._number_of_letters]
        new_lines = [word.replace("ё", "е") for word in new_lines]
        new_lines = list(set(new_lines))
        return new_lines

    def _load_words(self, filename="rus_words_no_duplicates.txt"):
        words_path = Path(__file__).resolve().parent / filename
        with words_path.open("r", encoding="utf-8") as f:
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
            for letter, min_count in self._known_letters.items():
                if word.count(letter) < min_count:
                    flag = False
                    break
            if not flag:
                continue
            for letter, max_count in self._max_letter_counts.items():
                if word.count(letter) > max_count:
                    flag = False
                    break
            if flag:
                RESULT_LIST.append(word)
        self._current_available_words = RESULT_LIST

    def _remove_letter_from_regular(self, letter, position=None):
        if position is None or self._known_letters.get(letter, 0) == 0:
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

        feedback_by_letter = defaultdict(list)
        for i, letter, state_of_letter in zip(range(len(word)), word, state_of_word):
            feedback_by_letter[letter].append((i, state_of_letter))
            if state_of_letter == "+":
                self._current_regular_expression[i] = letter
            elif state_of_letter == "*":
                self._current_regular_expression[i] = self._current_regular_expression[
                    i
                ].replace(letter, "")
            elif state_of_letter != "-":
                raise Exception("Wrong state")

        for letter, letter_feedback in feedback_by_letter.items():
            min_count = sum(
                1 for _, state_of_letter in letter_feedback if state_of_letter in ["+", "*"]
            )
            has_absent_occurrence = any(
                state_of_letter == "-" for _, state_of_letter in letter_feedback
            )

            if min_count > 0:
                self._known_letters[letter] = max(self._known_letters[letter], min_count)
            else:
                self._known_letters.pop(letter, None)
            if has_absent_occurrence:
                current_max = self._max_letter_counts.get(letter)
                if current_max is None:
                    self._max_letter_counts[letter] = min_count
                else:
                    self._max_letter_counts[letter] = min(current_max, min_count)

            if min_count == 0:
                self._remove_letter_from_regular(letter)
                continue

            for i, state_of_letter in letter_feedback:
                if state_of_letter == "-":
                    self._remove_letter_from_regular(letter, i)

        for i, letter, state_of_letter in zip(range(len(word)), word, state_of_word):
            if state_of_letter == "-":
                continue

        self._current_state += 1

        self._apply_regular()

#!/usr/bin/python

import random
import re
import sys
from collections import defaultdict
from typing import List


class Game:
    def __init__(self, n_letters=5) -> None:
        self._secret_word = None
        self._number_of_letters = n_letters
        # self._number_of_attempts = n_attempts
        self._current_state = 0

    def set_game(self, word):
        self._secret_word = word
        self._current_state = 0

    def get_response(self, word):
        assert len(word) == self._number_of_letters, "Wrong number of letters"

        self._current_state += 1
        state = ""
        for true_letter, guess_letter in zip(self._secret_word, word):
            if true_letter == guess_letter:
                state += "+"
            elif guess_letter in self._secret_word:
                state += "*"
            else:
                state += "-"
        return state


class FindAnswer:
    def __init__(self, n_letters=5) -> None:
        self._number_of_letters = n_letters
        self._all_letters = "абвгдежзийклмнопрстуфхцчшщъыьэюя"

        self._current_regular_expression = [self._all_letters] * self._number_of_letters
        self._known_letters = defaultdict(
            int
        )  # буквы которые точно должны быть в слове
        self._all_words = []
        self._current_available_words = []  # current pool of words

        self._previous_words_states = []  # полученные состояния по словам
        self._previous_words = []  # введенные слова
        self._load_words()

    def reset(self):
        self._previous_words.clear()
        self._previous_words_states.clear()
        self._known_letters.clear()
        self._current_available_words = self._all_words.copy()
        self._current_regular_expression = [self._all_letters] * self._number_of_letters

    def get_random_word(self):
        return random.choice(self._all_words)

    def _preprocessing_text(self, lines: List[str]):
        new_lines = [word.strip() for word in lines]
        new_lines = [word.lower() for word in new_lines if word.isalpha()]
        new_lines = [word for word in new_lines if len(word) == self._number_of_letters]
        new_lines = [word for word in new_lines if "ё" not in word]
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

        self._apply_regular()


def model_game(game: Game, predictor: FindAnswer, n_attempts: int = 6):
    n_letters = predictor._number_of_letters
    CORRECT_PREDICTION = "+" * n_letters
    for _ in range(n_attempts):
        try:
            predict_word = predictor.get_next_word()
        except Exception as e:
            print(f"Error: {e}")
            return False

        state = game.get_response(predict_word)
        if state == CORRECT_PREDICTION:
            return True
        predictor.response_from_game(word=predict_word, state_of_word=state)

    return False


if __name__ == "__main__":
    args = sys.argv

    if args[1] == "-model-game":
        if "-N" in args:
            index = args.index("-N")
            N = int(args[index + 1])
        else:
            N = 10
        n_attempts = 6
        predictor = FindAnswer(n_letters=5)
        game = Game(n_letters=5)
        # print("Всего слов: ", len(predictor._all_words)) 3759

        n_correct = 0
        unguessed_words = []
        history = []

        for _ in range(N):
            word = predictor.get_random_word()
            predictor.reset()
            game.set_game(word)
            result = model_game(game, predictor, n_attempts=n_attempts)
            if result:
                n_correct += 1
            else:
                unguessed_words.append(word)
                history.append(predictor._previous_words[-1])

        print(f"Winning percent: {n_correct / N:.3f} %")
        if len(unguessed_words) > 0:
            print(unguessed_words)
            print(history)

    elif args[1] == "-outer-game":
        n_letters = 5
        n_attempts = 6
        answer = FindAnswer(n_letters=n_letters)
        if "-regime" in args:
            index = args.index("-regime")
            regime = args[index + 1]
        else:
            regime = "auto"
        try:
            for _ in range(n_attempts):
                print(
                    f"Number of available words: {len(answer._current_available_words)}"
                )
                while True:
                    suggested_word = answer.get_next_word()
                    response = input(
                        f"Suggested word: {suggested_word}. Ok: (y) "
                    ).lower()
                    if response in ["y", "yes", "да"]:
                        break

                # response = input('Win? (y) ').lower()
                # if response in ['y', 'yes', 'да']:
                #     print("YEEEEEEEEEESSS!!!")
                #     break

                while True:
                    print("    Response.")
                    if regime == "auto":
                        word_response = suggested_word
                    else:
                        word_response = input("word: ").lower()
                    state_response = input("state: ")
                    if not len(word_response) == len(state_response) == n_letters:
                        print("Wrong input")
                        continue
                    break
                answer.response_from_game(
                    word=word_response, state_of_word=state_response
                )
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("\n                 Game is over")

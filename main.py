#!/usr/bin/python

import sys

from tqdm import tqdm

from predictor import FindAnswer


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


def model_game(
    game: Game, predictor: FindAnswer, n_attempts: int = 6, strategy="clever"
):
    n_letters = predictor._number_of_letters
    CORRECT_PREDICTION = "+" * n_letters
    for step in range(n_attempts):
        try:
            if strategy == "random":
                predict_word = predictor.get_next_word()
            elif strategy == "clever":
                predict_word = predictor.get_clever_random_word()
            else:
                raise Exception("Wrong strategy for choosing word")
        except Exception as e:
            print(f"Error: {e}")
            return False, n_attempts

        state = game.get_response(predict_word)
        if state == CORRECT_PREDICTION:
            return True, step + 1
        predictor.response_from_game(word=predict_word, state_of_word=state)

    return False, n_attempts


if __name__ == "__main__":
    args = sys.argv
    n_letters = 5
    n_attempts = 6

    if "-model-game" in args:
        if "-N" in args:
            index = args.index("-N")
            N = int(args[index + 1])
        else:
            N = 10

        strategy = "clever"
        if "-random" in args:
            strategy = "random"

        predictor = FindAnswer(n_letters=n_letters)
        game = Game(n_letters=n_letters)
        average_number_of_predictions = 0
        n_correct = 0
        unguessed_words = []
        history = []

        for _ in tqdm(range(N)):
            word = predictor.get_random_word()
            predictor.reset()
            game.set_game(word)
            result, steps = model_game(
                game, predictor, n_attempts=n_attempts, strategy=strategy
            )
            average_number_of_predictions += steps
            if result:
                n_correct += 1
            else:
                unguessed_words.append(word)
                history.append(predictor._previous_words[-1])

        print(f"Winning percent: {n_correct / N:.3f} %")
        print(f"Average number of predictions: {average_number_of_predictions / N:.2f}")

        if "-logs" in args and len(unguessed_words) > 0:
            print("Unguessed words:", unguessed_words)
            print("Last guesses: ", history)

    elif "-outer-game" in args:
        answer = FindAnswer(n_letters=n_letters)
        regime = "auto"
        strategy = "clever"

        if "-regime" in args:
            index = args.index("-regime")
            regime = args[index + 1]
        if "-random" in args:
            strategy = "random"
        try:
            for _ in range(n_attempts):
                print(
                    f"Number of available words: {len(answer._current_available_words)}"
                )
                while True:
                    if strategy == "clever":
                        suggested_word = answer.get_clever_random_word()
                    else:
                        suggested_word = answer.get_next_word()
                    response = input(
                        f"Suggested word: {suggested_word}. Ok: (y) "
                    ).lower()
                    if response in ["y", "yes", "да", "д"]:
                        break

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

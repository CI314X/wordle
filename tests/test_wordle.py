from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from main import Game, model_game
from predictor import FindAnswer


def make_finder(words):
    finder = FindAnswer()
    finder._all_words = list(words)
    finder._current_available_words = list(words)
    finder._current_regular_expression = [finder._all_letters] * finder._number_of_letters
    finder._known_letters.clear()
    finder._max_letter_counts.clear()
    finder._previous_words.clear()
    finder._previous_words_states.clear()
    finder._current_state = 0
    finder._current_available_words_with_probs.clear()
    finder._count_probs_call = 0
    return finder


def test_game_returns_expected_feedback_for_simple_guess():
    game = Game()
    game.set_game("лампа")

    assert game.get_response("лапка") == "++*-+"


def test_model_game_stops_after_successful_guess():
    class StubPredictor:
        _number_of_letters = 5

        def __init__(self):
            self.calls = []

        def get_clever_random_word(self):
            return "лампа"

        def response_from_game(self, word, state_of_word):
            self.calls.append((word, state_of_word))

    predictor = StubPredictor()
    game = Game()
    game.set_game("лампа")

    result, steps = model_game(game, predictor, n_attempts=6, strategy="clever")

    assert result is True
    assert steps == 1
    assert predictor.calls == []


def test_response_from_game_filters_candidates_with_fixed_and_absent_letters():
    finder = make_finder(["абвгд", "аежзи", "ажзик", "клмно"])

    finder.response_from_game(word="абвгд", state_of_word="+----")

    assert finder._current_available_words == ["аежзи", "ажзик"]


def test_response_from_game_keeps_known_letter_but_removes_wrong_position():
    finder = make_finder(["еажзи", "аежзи", "клмно"])

    finder.response_from_game(word="абвгд", state_of_word="*----")

    assert finder._current_available_words == ["еажзи"]


def test_reset_restores_initial_state():
    finder = make_finder(["абвгд", "аежзи"])
    finder.response_from_game(word="абвгд", state_of_word="+----")

    finder.reset()

    assert finder._current_state == 0
    assert finder._previous_words == []
    assert finder._previous_words_states == []
    assert finder._known_letters == {}
    assert finder._current_available_words == ["абвгд", "аежзи"]


def test_load_words_normalizes_length_case_duplicates_and_yo():
    finder = FindAnswer()

    lines = [" Ёжик\n", "ежик\n", "ДОМ\n", "абв12\n", " лампа \n", "ЛАМПА\n", "Ёлка\n"]

    assert sorted(finder._preprocessing_text(lines)) == ["лампа"]


def test_game_feedback_handles_repeated_letters_like_wordle():
    game = Game()
    game.set_game("мамба")

    assert game.get_response("ааааа") == "-+--+"


def test_find_answer_can_be_created_outside_project_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    finder = FindAnswer()

    assert len(finder._all_words) > 0
    assert Path("rus_words_no_duplicates.txt").exists() is False


def test_response_from_game_limits_max_count_for_repeated_letters():
    finder = make_finder(["абвгд", "аабвг", "акала"])

    finder.response_from_game(word="ааааа", state_of_word="+----")

    assert finder._current_available_words == ["абвгд"]


def test_outer_game_stops_immediately_after_full_match():
    process = subprocess.run(
        [sys.executable, "main.py", "-outer-game"],
        input="y\n+++++\n",
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=True,
    )

    assert process.stdout.count("Suggested word:") == 1
    assert "Word is guessed" in process.stdout

"""テスト"""

# flake8: noqa: S101
from textwrap import dedent

from nicegui_reversi import Game


def test_place_disk() -> None:
    """ディスクを置いたときのテスト"""
    before = dedent("""\
        player = "Black"
        board = [
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 2, 1, 0, 0, 0],
          [0, 0, 0, 1, 2, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
        ]""")
    after = dedent("""\
        player = "Black"
        board = [
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 1, 1, 1, 0, 0, 0],
          [0, 0, 0, 1, 2, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
        ]""")
    reversi = Game(before, save_to_storage=False)
    place_ok = reversi.place_disk(3 + 4 * 9)
    assert place_ok
    assert reversi.to_toml() == after

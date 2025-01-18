# flake8: noqa: S101
from textwrap import dedent

from nicegui_reversi import Game


def test_place_disk():
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
    reversi = Game()
    reversi.from_toml(before)
    result = reversi.place_disk(3 + 4 * 9)
    assert result
    assert reversi.to_toml() == after

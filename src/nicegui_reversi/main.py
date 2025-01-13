import tomllib
from collections.abc import Iterator
from enum import IntEnum
from pathlib import Path
from typing import ClassVar

import numpy as np
from nicegui import elements, ui


class State(IntEnum):
    Empty = 0
    Black = 1
    White = 2
    OK = 3

    def opponent(self) -> "State":
        return State.Black if self == State.White else State.White


class Square(ui.element):
    chars: ClassVar[list[str]] = ["", "⚫️", "⚪️", "・"]

    def __init__(self, reversi: "Reversi", index: int):
        super().__init__("div")
        self.reversi = reversi
        self.index = index

    def build(self, value: State) -> None:
        self.clear()  # 子要素をクリア
        with self:
            classes = "w-9 h-9 text-3xl text-center border border-black"
            ui.label(self.chars[value]).classes(classes).on("click", lambda: self.reversi.click(self))


class Reversi:
    player: State = State.Black
    board: np.ndarray
    message: str = ""
    squares: list[Square]
    pass_button: elements.button.Button
    SAVE_FILE: ClassVar[str] = "reversi.toml"

    def __init__(self):
        ui.label().bind_text(self, "message").classes("text-4xl")
        with ui.grid(columns=8).classes("gap-0 bg-green"):
            self.squares = [Square(self, x + y * 10) for y in range(1, 9) for x in range(1, 9)]
        with ui.row():
            ui.button("Reset", on_click=self.reset)
            self.pass_button = ui.button("Pass", on_click=self.pass_)
            self.pass_button.disable()
            ui.button("Load", on_click=self.load)
            ui.button("Save", on_click=self.save)
        self.reset()

    def reset(self) -> None:
        self.set_player(State.Black)
        self.board = np.full(100, State.Empty, dtype=np.int8)
        self.board[45:55:9] = 1
        self.board[44:56:11] = 2
        self.rebuild()

    def set_player(self, player: State) -> None:
        self.player = player
        self.message = f"{self.player.name}'s turn"

    @classmethod
    def check_ok(cls, player: State, board: np.ndarray) -> bool:
        """置けるところをチェックし、置けるかを返す"""
        for y in range(1, 9):
            for x in range(1, 9):
                index = x + y * 10
                if board[index] % 3 == 0:
                    last_and_diffs = list(cls.calc_last_and_diff(index, player, board))
                    board[index] = bool(last_and_diffs) * 3
        return (board == State.OK).any()  # 置けるところがあるかどうか

    def rebuild(self) -> None:
        """置けるところをチェックし、Squareの再作成"""
        exist_ok = self.check_ok(self.player, self.board)
        for square in self.squares:
            square.build(self.board[square.index])
        self.pass_button.set_enabled(not exist_ok)

    def pass_(self) -> None:
        self.set_player(self.player.opponent())
        self.check_ok(self.player, self.board)
        self.rebuild()

    def save(self) -> None:
        with Path(self.SAVE_FILE).open("w", encoding="utf-8") as fp:
            fp.write(f'player = "{self.player.name}"\n')
            fp.write("board = [\n")
            for i in range(1, 9):
                s, e = i * 10 + 1, i * 10 + 9
                fp.write(f"  {(self.board[s:e] % 3).tolist()},\n")
            fp.write("]\n")

    def load(self) -> None:
        with Path(self.SAVE_FILE).open("rb") as fp:
            dc = tomllib.load(fp)
        self.set_player(State[dc["player"]])
        board = np.full((10, 10), State.Empty, dtype=np.int8)
        board[1:9, 1:9] = dc["board"]
        self.board = board.flatten()
        self.rebuild()
        self.judge()

    def click(self, target: Square) -> None:
        if self.board[target.index] % 3 or not self.place_disk(target.index):
            return
        self.board[target.index] = self.player
        self.set_player(self.player.opponent())
        self.rebuild()
        self.judge()

    def judge(self) -> None:
        if (self.board % 3 == 0).any():
            if not self.pass_button.enabled:
                return
            board = self.board.copy()
            if self.check_ok(self.player.opponent(), board):
                return
        self.pass_button.disable()
        n_black = (self.board == State.Black).sum()
        n_white = (self.board == State.White).sum()

        self.message = (
            "Draw"
            if n_black == n_white
            else f"Black won!({n_black} > {n_white})"
            if n_black > n_white
            else f"White won!({n_white} > {n_black})"
        )

    @classmethod
    def calc_last_and_diff(cls, index: int, player: State, board: np.ndarray) -> Iterator[tuple[int, int]]:
        opponent = player.opponent()
        for diff in [-11, -10, -9, -1, 1, 9, 10, 11]:
            for cnt in range(1, 9):
                last = index + diff * cnt
                value = board[last]
                if value != opponent:
                    if cnt > 1 and value == player:
                        yield last, diff
                    break

    def place_disk(self, index: int) -> bool:
        last_and_diffs = list(self.calc_last_and_diff(index, self.player, self.board))
        if not last_and_diffs:
            return False
        self.board[index] = self.player
        for last, diff in last_and_diffs:
            self.board[index:last:diff] = self.player
        return True


def main(*, reload=False, port=8101):
    Reversi()
    ui.run(title="Reversi", reload=reload, port=port)

import tomllib
from collections.abc import Iterable
from enum import IntEnum
from itertools import product
from pathlib import Path
from typing import ClassVar

import numpy as np
from nicegui import app, elements, ui


class State(IntEnum):
    """マスの状態または手番"""

    Empty = 0
    Black = 1
    White = 2
    OK = 3  # 手番で置けるか

    def opponent(self) -> "State":
        """Black <-> White"""
        return State.Black if self == State.White else State.White


def ok_to_empty[T](board: T) -> T:  # Tはintまたはnp.ndarray
    """State.OK(3)であればState.Empty(0)に変換する"""
    return board % 3  # type: ignore[operator, return-value]


class Square(ui.element):
    """GUI部品としてのマス"""

    def __init__(self, game: "Game", index: int):
        super().__init__("div")
        self.game = game
        self.index = index
        classes = "w-9 h-9 text-3xl text-center border border-black cursor-default"
        with self:
            ui.label().bind_text(self, "text").classes(classes).on("click", lambda: game.click(index))

    @property
    def text(self):
        """表示する文字"""
        chars = ["", "⚫️", "⚪️", "・"]
        return chars[self.game.board[self.index]]


class Game:
    """リバーシゲーム"""

    player: State  # 手番
    board: np.ndarray  # 10*9+1個の1次元配列
    message: str  # 手番や勝敗の表示
    squares: list[Square]  # 64個のマス
    pass_button: elements.button.Button  # PASSボタン
    save_to_storage: bool  # 変更時にゲームの状態を保存するかどうか
    SAVE_FILE: ClassVar[str] = "reversi.toml"  # ファイル名

    def __init__(self, toml: str | None, *, save_to_storage: bool = True):
        self.board = np.zeros(91, dtype=np.int8)
        self.message = ""
        self.save_to_storage = save_to_storage
        ui.label().bind_text(self, "message").classes("text-3xl")
        with ui.grid(columns=8).classes("gap-0 bg-green"):
            self.squares = [Square(self, x + y * 9) for y in range(1, 9) for x in range(1, 9)]
        with ui.row():
            ui.button("reset", on_click=self.reset)
            self.pass_button = ui.button("pass", on_click=self.pass_)
            ui.button("load", on_click=self.load_file)
            ui.button("save", on_click=self.save_file)
        if toml:
            self.from_toml(toml)
        else:
            self.reset()

    def reset(self) -> None:
        """ゲームの初期化"""
        self.set_player(State.Black)
        self.board[:] = State.Empty
        self.board[41:51:8] = State.Black
        self.board[40:52:10] = State.White
        self.set_pass_button()
        self.save()

    def set_player(self, player: State) -> None:
        """手番設定"""
        self.player = player
        self.message = f"{self.player.name}'s turn"

    @classmethod
    def set_ok(cls, player: State, board: np.ndarray) -> bool:
        """置けるマスを設定し、置けるかを返す"""
        for y, x in product(range(1, 9), range(1, 9)):
            index = x + y * 9
            if not ok_to_empty(board[index]):  # Empty or OK
                can_place = any(cls.calc_last_and_diff(index, player, board))
                board[index] = State.OK if can_place else State.Empty
        return (board == State.OK).any()  # 置けるマスがあるかどうか

    def set_pass_button(self) -> None:
        """State.OKが1つもなければ、パスできるようにする"""
        self.pass_button.set_enabled(not self.set_ok(self.player, self.board))

    def pass_(self) -> None:
        """パス処理"""
        self.set_player(self.player.opponent())
        self.set_ok(self.player, self.board)
        self.set_pass_button()
        self.save()

    def to_toml(self) -> str:
        """ゲームの状態をTOML化"""
        lst = [f'player = "{self.player.name}"', "board = ["]
        lst.extend(f"  {ok_to_empty(self.board[i * 9 + 1 : i * 9 + 9]).tolist()}," for i in range(1, 9))
        lst.append("]")
        return "\n".join(lst)

    def from_toml(self, toml: str) -> None:
        """TOMLからゲームの状態を復元"""
        dc = tomllib.loads(toml)
        self.set_player(State[dc["player"]])
        board = np.full((10, 9), State.Empty, dtype=np.int8)
        board[1:9, 1:9] = dc["board"]
        self.board = np.hstack([board.flatten(), [0]])
        self.set_pass_button()
        self.judge()
        self.save()

    def save(self) -> None:
        """ゲームの状態をストレージに保存"""
        if self.save_to_storage:
            app.storage.tab["game"] = self.to_toml()

    def save_file(self) -> None:
        """ゲームの状態をファイルに保存"""
        Path(self.SAVE_FILE).write_text(self.to_toml(), encoding="utf-8")

    def load_file(self) -> None:
        """ファイルからゲームの状態を読込"""
        self.from_toml(Path(self.SAVE_FILE).read_text(encoding="utf-8"))

    def click(self, index: int) -> None:
        """マスのクリック"""
        if self.board[index] == State.OK:
            self.board[index] = self.player
            self.place_disk(index)
            self.set_player(self.player.opponent())
            self.set_pass_button()
            self.judge()
            self.save()

    def judge(self) -> None:
        """終局判定"""
        if not self.pass_button.enabled:  # パスできない(=置けるマスあり)
            return
        if (self.board == State.Empty).any():  # 空きマスあり
            board = self.board.copy()
            if self.set_ok(self.player.opponent(), board):  # 相手は置ける
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
    def calc_last_and_diff(cls, index: int, player: State, board: np.ndarray) -> Iterable[tuple[int, int]]:
        """indexに置いたとき、8方向ごとにどれだけひっくり返せるか

        :param index: boardの位置
        :param player: 手番
        :param board: 盤面
        :yield: 「挟むための自分のディスクの位置」と方向(差分)
        """
        opponent = player.opponent()
        for diff in [-10, -9, -8, -1, 1, 8, 9, 10]:
            for cnt in range(1, 9):
                last = index + diff * cnt
                value = board[last]
                if value != opponent:
                    if cnt > 1 and value == player:
                        yield last, diff
                    break

    def place_disk(self, index: int) -> bool:
        """ディスクを置く"""
        last_and_diffs = list(self.calc_last_and_diff(index, self.player, self.board))
        if not last_and_diffs:
            return False
        self.board[index] = self.player
        for last, diff in last_and_diffs:
            self.board[index:last:diff] = self.player
        return True


@ui.page("/")
async def top_page():
    """トップページ"""
    await ui.context.client.connected()
    Game(app.storage.tab.get("game"))


def main(*, reload=False, port=8102):  # noqa: D103
    ui.run(title="Reversi", reload=reload, port=port)

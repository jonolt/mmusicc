import curses
import enum

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

from mmusicc import mmusicc, metadata

# TODO: tags to be written must be defined in a dictionary and not created on
#  the fly, simliar to overwrite dict, should be provided bei MusicManager
#  and/or Metadata eg
#       Text->"tag text"--> return string by Metadata
#       None->"<None>", --> retrun string by Metadata
#       Empty->"Empty", --> retrun string by Metadata
#       Different->"~", --> return string by meta album proxy
#   tui does not need to know what the srings mean, only has to compare, maybe
#   comparision is better at MediaManager

# TODO: future to austoskip objects where nothing is overwritten

class Tui:

    data_start = 6
    divider_size = [5, 5, 5, 5, ]
    divider = None
    col_source_start = 19
    col_writer_start = 73
    col_target_start = 76
    length_tag_str = 52

    dict_tag_pos = None
    list_displ_tags = None

    @classmethod
    def init_class(cls):
        cls.list_displ_tags = metadata.Metadata.get_dictionaries().get(
            "list_displ_tags")
        cls.dict_tag_pos = dict()
        cls.divider = [6]
        for size in cls.divider_size:
            cls.divider.append(cls.divider[-1] + size + 1)
        i = 1
        j = cls.divider[0]
        while i <= len(cls.list_displ_tags):
            pos = i + j
            if pos in cls.divider:
                j += 1
                continue
            tag = cls.list_displ_tags[i-1]
            if tag:
                cls.dict_tag_pos[tag] = pos
            i += 1
        cls.list_displ_tags.insert(0, "TAG")
        cls.dict_tag_pos["TAG"] = cls.data_start - 2

    # TODO clean up OLD, replace with dynamic variables
    f_str_tags = "{:<15}:"
    f_str_head = "{:^15}: {:^52} [ ] {:^52}"
    f_str_path = "{:>109}"
    f_str_meta = "{:<52} [ ] {:<52}"  # start at col2 start

    f_str_tags_pos = 2
    f_str_head_pos = 2
    f_str_path_pos = 19
    f_str_bckd_pos = 73
    f_str_meta_pos = 19

    def __init__(self, mm=None):
        Tui.init_class()
        if mm:
            self._mm = mm
        else:
            self._mm = mmusicc.MusicManager()
        self._line_focus = "TAG"
        print("LOADED TUI")

    def main(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        self.stdscr = stdscr
        self._init_curses()
        curses.curs_set(0)

        self.__update_window_size()
        self.__create_windows()
        self.win_head.addstr(1, 1, "Hallo, Welt! {}x{}"
                             .format(self.maxx, self.maxy))
        self.stdscr.refresh()
        self.win_head.refresh()

        self.main_static()
        self.update_overwrite()

        # Maus initialisieren
        avail, oldmask = curses.mousemask(curses.BUTTON1_PRESSED)
        curses.mousemask(avail)

        while True:
            c = stdscr.getch()
            if c == ord('x') or c == ord('q'):
                break
            elif c == curses.KEY_DOWN:
                stdscr.addstr(0, 1, "KEY_DOWN")
                self.__move_curser(-1)
            elif c == curses.KEY_UP:
                stdscr.addstr(0, 1, "KEY_UP")
                self.__move_curser(+1)
            elif c == curses.KEY_LEFT:
                stdscr.addstr(0, 1, "KEY_LEFT")
                stdscr.addstr(0, 1, "KEY_RIGHT")
                if self._line_focus == "TAG":
                    self._mm.overwrite_dict.disable_all()
                else:
                    self._mm.overwrite_dict.disable(self._line_focus)
                self.update_overwrite()
            elif c == curses.KEY_RIGHT:
                stdscr.addstr(0, 1, "KEY_RIGHT")
                if self._line_focus == "TAG":
                    self._mm.overwrite_dict.enable_all()
                else:
                    self._mm.overwrite_dict.enable(self._line_focus)
                self.update_overwrite()
            elif c == ord('t'):
                if self._line_focus == "TAG":
                    self._mm.overwrite_dict.toggle_all()
                else:
                    self._mm.overwrite_dict.toggle(self._line_focus)
                self.update_overwrite()
            elif c == curses.KEY_MOUSE:
                try:
                    id, x, y, z, button = curses.getmouse()
                    s = "Mouse-Ereignis bei (%d ; %d ; %d)" % (x, y, z)
                    stdscr.addstr(0, 1, s)
                    stdscr.clrtoeol()
                    stdscr.refresh()
                except curses.error:
                    continue
        
            self.__update_data()
            self.win_main.refresh()

    def __move_curser(self, step):
        i = Tui.list_displ_tags.index(self._line_focus)
        i = i - step
        if i >= len(Tui.list_displ_tags):
            i = i - len(Tui.list_displ_tags)
        if i < 0:
            i = i + len(Tui.list_displ_tags)
        self._line_focus = Tui.list_displ_tags[i]
        self.update_overwrite()

    def __update_data(self):
        if self._mm.source and self._mm.target:
            for tag in Tui.list_displ_tags:
                if tag == "TAG":
                    continue
                self.__update_tag(tag)

    def __update_tag(self, tag):
        tag_s = self._mm.source_meta_dict.get(tag)
        tag_t = self._mm.target_meta_dict.get(tag)
        if not tag_s:
            tag_s = "<None>"
        if not tag_t:
            tag_t = "<None>"
        color_pair_t = ColorPair.normal
        if self._mm.overwrite_dict.get(tag):
            if tag_s == tag_t:
                color_pair_t = ColorPair.normal
            else:
                if tag_t == "" or tag_t == "<None>" or None:
                    color_pair_t = ColorPair.new
                else:
                    color_pair_t = ColorPair.overwrite
        # write source TODO add autocomlete color blue
        self.__str_writer(
            line=Tui.dict_tag_pos.get(tag),
            col=Tui.col_source_start,
            text=tag_s,
            length=Tui.length_tag_str
        )
        self.__str_writer(
            line=Tui.dict_tag_pos.get(tag),
            col=Tui.col_target_start,
            text=tag_t,
            length=Tui.length_tag_str,
            color_pair=color_pair_t.value[0]
        )

    def __str_writer(self, line, col, text, length, align="<", color_pair=1):
        text = Tui.__string_cut(text, length, at_newline=True)
        str_format = "{:" + align + str(length) + "}"
        str_diplay = str_format.format(text)
        self.win_main.addstr(line, col, str_diplay,
                             curses.color_pair(color_pair))

    @staticmethod
    def __string_cut(text, length, at_newline=False):
        if not text:
            text = ""
        if at_newline and not text == "":
            text = text.splitlines()[0]
        if len(text) > length:
            text = text[len(text)-length:]
        return text

    def update_overwrite(self):
        for tag in self.dict_tag_pos.keys():
            self.displ_write(tag)

    def displ_write(self, tag, focus=False):
        if focus or self._line_focus == tag:
            style = curses.A_REVERSE
        else:
            style = curses.A_NORMAL
        if self._mm.overwrite_dict.get(tag):
            self.win_main.addstr(Tui.dict_tag_pos[tag], Tui.f_str_bckd_pos-1, "[>]", style)
        else:
            self.win_main.addstr(Tui.dict_tag_pos[tag], Tui.f_str_bckd_pos-1, "[ ]", style)
        self.win_main.refresh()

    def main_static(self):
        self.win_main.hline(3, 1, '+', 128)
        for div in Tui.divider[:-1]:
            self.win_main.hline(div, 1, '-', 128)
        self.win_main.hline(Tui.divider[-1], 1, '+', 128)
        tmp_str_head = Tui.f_str_head\
            .format("TAG", "METADATA SOURCE", "METADATA TARGET")
        self.win_main.addstr(Tui.dict_tag_pos.get("TAG"), Tui.f_str_head_pos, tmp_str_head)
        self.win_main.addstr(1, Tui.f_str_tags_pos,
            Tui.f_str_tags.format("SOURCE"))
        self.win_main.addstr(2, Tui.f_str_tags_pos,
            Tui.f_str_tags.format("TARGET"))
        for tag_name in Tui.dict_tag_pos.keys():
            self.win_main.addstr(
                Tui.dict_tag_pos.get(tag_name),
                Tui.f_str_tags_pos,
                Tui.f_str_tags.format(tag_name))
        self.win_main.refresh()

    def __create_windows(self):
        if self.maxx:
            x_offset = int((self.maxx-130)/2)
            if x_offset < 0:
                x_offset = 0
        else:
            x_offset = 0
        if self.maxy:
            y_offset = int((self.maxy-45)/2)
            if y_offset < 0:
                y_offset = 0
        else:
            y_offset = 0
        self.win_head = curses.newwin(5, 130, y_offset, x_offset)
        self.win_head.bkgd(curses.color_pair(ColorPair.standard_ui.value[0]))
        self.win_head.box()
        self.win_head.addstr(0, int(130 / 2 - 12), "Metadata Music Control")
        self.win_head.refresh()
        self.win_main = curses.newwin(40 - 5, 130, y_offset+5, x_offset)
        self.win_main.bkgd(curses.color_pair(ColorPair.standard_ui.value[0]))
        self.win_main.box()
        self.win_main.refresh()

    def _init_curses(self):
        curses.start_color()
        curses.init_pair(ColorPair.standard_ui.value[0], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.normal.value[0], curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.overwrite.value[0], curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.new.value[0], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.autofill.value[0], curses.COLOR_CYAN, curses.COLOR_BLACK)
        self.stdscr.refresh()

    def __update_window_size(self):
        self.maxy, self.maxx = self.stdscr.getmaxyx()


class ColorPair(enum.Enum):
    standard_ui = 1,
    normal = 2,
    overwrite = 3,
    new = 4,
    autofill = 42,

# TODO conetnt None, Empty, Different (bei gruppen)


if __name__ == "__main__":
    Tui().main()

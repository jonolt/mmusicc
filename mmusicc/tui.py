import curses


class Tui:
    """

    will be started from music manager module
    --> how to pass objects/properties
    --> you should be able to run mmusicc with and without cli
    """

    color_pair_head_colors = (curses.COLOR_BLACK, curses.COLOR_YELLOW)
    color_pair_main_colors = (curses.COLOR_YELLOW, curses.COLOR_BLACK)
    color_pair_main_colors_unchanged = (curses.COLOR_WHITE, curses.COLOR_BLACK)
    color_pair_main_colors_autofill = (curses.COLOR_BLUE, curses.COLOR_BLACK)
    color_pair_main_colors_changed = (curses.COLOR_YELLOW, curses.COLOR_BLACK)
    color_pair_main_colors_delete = (curses.COLOR_RED, curses.COLOR_BLACK)
    _color_head = 1
    _color_main = 2

    col_1_width = 16
    col_2_width = 52
    col_3_width = 52
    col_1_start_ = 6
    col_2_start_ = col_1_start_ + col_1_width + 1
    col_3_start_ = col_2_start_ + col_2_width + 1

    dict_tag = {
        'TAG': 1,
        'SCR': 2,
        'TALB': 4,
        'TDRC': 5,
        'TPE1': 6,
        'TPE2': 7,
        'TRCK': 8,
        'TIT2': 10,
        'TCON': 11,
        'USLT': 12,
        'COMM': 13,
        'TBPM': 14,
        'TCOM': 16,
        'TPOS': 17,
        'TSRC': 18,
        'DISCID': 19,
        'DISKTOT': 20,
        'TRKTOT': 22,
    }

    dict_name = {
        'TAG': 'TAG',
        'SCR': 'file/db',
        'TALB': 'ALBUM',
        'TDRC': 'YEAR',
        'TPE1': 'ARTIST',
        'TPE2': 'ALBUMARTIST',
        'TRCK': 'TRACKNUMBER',
        'TIT2': 'TITLE',
        'TCON': 'GENRE',
        'USLT': 'LYRICS',
        'COMM': 'DESCRIPTION',
        'TBPM': 'BPM',
        'TCOM': 'COMPOSER',
        'TPOS': 'DISCNUMBER',
        'TSRC': 'ISRC',
        'DISCID': 'DISCID',
        'DISKTOT': 'DISCTOTAL',
        'TRKTOT': 'TRACKTOTAL',
    }

    def __init__(self):
        pass

    def main(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        self.stdscr = stdscr
        self._init_curses()

        self.__update_window_size()
        self.__create_windows()
        self.win_head.addstr(1, 1, "Hallo, Welt! {}x{}"
                             .format(self.maxx, self.maxy))
        self.stdscr.refresh()
        self.win_head.refresh()

        self.main_header()

        while True:
            c = stdscr.getch()
            if c == ord('x') or c == ord('q'):
                break
            elif c == ord('t'):
                self.tag_line("TALB", True, "fuu", "bar")

    def tag_line(self, tag, write_enabled, meta_write, meta_org):
        if not isinstance(write_enabled, type(None)):
            self.set_write(tag, write_enabled)
        self.win_main.addstr(Tui.dict_tag[tag], Tui.col_2_start_,
                             "{:<52}".format(meta_write))
        self.win_main.addstr(Tui.dict_tag[tag], Tui.col_3_start_,
                             "{:<52}".format(meta_org))
        self.win_main.refresh()

    def main_header(self):
        self.tag_line("TAG", None, "METADATA TO BE WRITTEN",
                      "METADATA ORIGINAL")
        self.win_main.hline(3, 1, '-', 128)
        self.win_main.hline(9, 1, '-', 128)
        self.win_main.hline(15, 1, '-', 128)
        self.win_main.hline(21, 1, '-', 128)
        self.win_main.hline(27, 1, '_', 128)
        for tag in Tui.dict_tag.keys():
            self.win_main.addstr(Tui.dict_tag[tag], Tui.col_1_start_,
                                 "{:<16}".format(Tui.dict_name[tag]))
        self.win_main.refresh()

    def set_write(self, tag, write_enabled):
        if write_enabled:
            self.win_main.addstr(Tui.dict_tag[tag], 2, "[X]")
        else:
            self.win_main.addstr(Tui.dict_tag[tag], 2, "[ ]")

    def __create_windows(self):
        if self.maxx:
            x_offset = int((self.maxx-130)/2)
        else:
            x_offset = 0
        if self.maxy:
            y_offset = int((self.maxy-45)/2)
        else:
            y_offset = 0
        self.win_head = curses.newwin(5, 130, y_offset, x_offset)
        self.win_head.bkgd(curses.color_pair(self._color_head))
        self.win_head.box()
        self.win_head.addstr(0, int(130 / 2 - 12), "Metadata Music Control")
        self.win_head.refresh()
        self.win_main = curses.newwin(40 - 5, 130, y_offset+5, x_offset)
        self.win_main.bkgd(curses.color_pair(self._color_main))
        self.win_main.box()
        self.win_main.refresh()

    def _init_curses(self):
        curses.start_color()
        curses.init_pair(Tui._color_head, *Tui.color_pair_head_colors)
        curses.init_pair(Tui._color_main, *Tui.color_pair_main_colors)
        self.stdscr.refresh()

    def __update_window_size(self):
        self.maxy, self.maxx = self.stdscr.getmaxyx()


if __name__ == "__main__":
    Tui().main()

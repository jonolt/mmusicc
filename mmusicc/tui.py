import curses

from mmusicc import mmusicc


class Tui:
    """

    will be started from music manager module
    --> how to pass objects/properties
    --> you should be able to run mmusicc with and without cli
    TODO add display of unsynced tags
    """

    color_pair_head_colors = (curses.COLOR_BLACK, curses.COLOR_YELLOW)
    color_pair_main_colors = (curses.COLOR_YELLOW, curses.COLOR_BLACK)
    color_pair_main_colors_unchanged = (curses.COLOR_WHITE, curses.COLOR_BLACK)
    color_pair_main_colors_autofill = (curses.COLOR_BLUE, curses.COLOR_BLACK)
    color_pair_main_colors_changed = (curses.COLOR_YELLOW, curses.COLOR_BLACK)
    color_pair_main_colors_delete = (curses.COLOR_RED, curses.COLOR_BLACK)
    _color_head = 1
    _color_main = 2

    f_str_tags = "{:<15}:"
    f_str_head = "{:^15}: {:^52} [ ] {:^52}"
    f_str_path =         "{:>109}"
    f_str_meta =         "{:<52} [ ] {:<52}"  # start at col2 start

    f_str_tags_pos = 2
    f_str_head_pos = 2
    f_str_path_pos = 19
    f_str_meta_pos = 19
    f_str_bckd_pos = 73

    offset = 1
    dict_tag = {
        # 1 + offset
        # 2 + offset
        'TAG': 3 + offset,
        # 4 + offset
        'TALB': 5 + offset,  # Album
        'TDRC': 6 + offset,  # Year
        'TPE2': 7 + offset,  # Album Artist
        'TCON': 8 + offset,  # Genre
        'TRKTOT': 9 + offset,  # Tracktotal
        # 10 + offset
        'TRCK': 11 + offset,  # Track Number
        'TIT2': 12 + offset,  # Title
        'TPE1': 13 + offset,  # Artist
        'TCOM': 14 + offset,  # Composer
        'TSRC': 15 + offset,  # ISRC
        # 16
        'USLT': 17 + offset,  # Lyrics
        'COMM': 18 + offset,  # Description
        'TBPM': 19 + offset,  # BPM
        # 20 + offset
        # 21 + offset
        # 22 + offset
        'TPOS': 23 + offset,  # Discnumber
        'DISKTOT': 24 + offset,  # Disctotal
        'DISCID': 25 + offset,  # Disc ID
        # 26 + offset
        # 27 + offset
    }

    # TODO make sure list is sorted
    list_sorted_tags = list(dict_tag.keys())

    dict_name = {
        'TAG': 'TAG',
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

    def __init__(self, mm=None):
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
                    s = "Mouse-Ereignis bei (%d ; %d ; %d), ID= %d, button = %d" % (
                    x, y, z, id, button)
                    stdscr.addstr(0, 1, s)
                    stdscr.clrtoeol()
                    stdscr.refresh()
                except curses.error:
                    continue

            self.update_data()
            self.win_main.refresh()

    def __move_curser(self, step):
        i = Tui.list_sorted_tags.index(self._line_focus)
        i = i - step
        if i >= len(Tui.list_sorted_tags):
            i = i - len(Tui.list_sorted_tags)
        if i < 0:
            i = i + len(Tui.list_sorted_tags)
        self._line_focus = Tui.list_sorted_tags[i]
        self.update_overwrite()

    def __string_cut(self, text, length, at_newline=False):
        if not text:
            text = ""
        if at_newline and not text=="":
            text = text.splitlines()[0]
        if len(text) > length:
            text = text[len(text)-length:]
        return text

    def update_data(self):
        if self._mm.source:
            meta_s = self._mm.source[0]
            meta_t = self._mm.target[0]
            self.win_main.addstr(1, Tui.f_str_path_pos, Tui.f_str_path.format(self.__string_cut(meta_s.file, 109)))
            self.win_main.addstr(2, Tui.f_str_path_pos, Tui.f_str_path.format(self.__string_cut(meta_t.file, 109)))
            self.tag_line('TALB', meta_s.TALB, meta_t.TALB)
            self.tag_line('TDRC', meta_s.TDRC, meta_t.TDRC)
            self.tag_line('TPE1', meta_s.TPE1, meta_t.TPE1)
            self.tag_line('TPE2', meta_s.TPE2, meta_t.TPE2)
            self.tag_line('TIT2', meta_s.TIT2, meta_t.TIT2)
            self.tag_line('TCON', meta_s.TCON, meta_t.TCON)
            self.tag_line('USLT', meta_s.USLT, meta_t.USLT)
            self.tag_line('COMM', meta_s.COMM, meta_t.COMM)
            self.tag_line('TPOS', meta_s.TPOS, meta_t.TPOS)
            self.tag_line('TSRC', meta_s.TSRC, meta_t.TSRC)
            self.tag_line('DISCID', meta_s.DISCID, meta_t.DISCID)
            self.tag_line('DISKTOT', meta_s.DISKTOT, meta_t.DISKTOT)
            self.tag_line('TRKTOT', meta_s.TRKTOT, meta_t.TRKTOT)
        self.win_main.refresh()

    def update_overwrite(self):
        for tag in self.dict_tag.keys():
            self.displ_write(tag)

    def tag_line(self, tag, text_s, text_t):
        text_s = self.__string_cut(text_s, 52, at_newline=True)
        text_t = self.__string_cut(text_t, 52, at_newline=True)
        self.win_main.addstr(Tui.dict_tag[tag], Tui.f_str_meta_pos,
                             Tui.f_str_meta.format(text_s, text_t))
        self.displ_write(tag)

    def displ_write(self, tag, focus=False):
        if focus or self._line_focus == tag:
            style = curses.A_REVERSE
        else:
            style = curses.A_NORMAL
        if self._mm.overwrite_dict.get(tag):
            self.win_main.addstr(Tui.dict_tag[tag], Tui.f_str_bckd_pos-1, "[>]", style)
        else:
            self.win_main.addstr(Tui.dict_tag[tag], Tui.f_str_bckd_pos-1, "[ ]", style)
        self.win_main.refresh()


    def main_static(self):
        self.win_main.hline(3, 1, '_', 128)
        self.win_main.hline(5, 1, '-', 128)
        self.win_main.hline(11, 1, '-', 128)
        self.win_main.hline(17, 1, '-', 128)
        self.win_main.hline(23, 1, '-', 128)
        self.win_main.hline(29, 1, '_', 128)
        tmp_str_head = Tui.f_str_head\
            .format("TAG", "METADATA SOURCE", "METADATA TARGET")
        self.win_main.addstr(4, Tui.f_str_head_pos, tmp_str_head)
        self.win_main.addstr(1, Tui.f_str_tags_pos,
            Tui.f_str_tags.format("SOURCE"))
        self.win_main.addstr(2, Tui.f_str_tags_pos,
            Tui.f_str_tags.format("TARGET"))
        for tag in Tui.dict_tag.keys():
            self.win_main.addstr(
                Tui.dict_tag[tag],
                Tui.f_str_tags_pos,
                Tui.f_str_tags.format(Tui.dict_name[tag]))
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
        #curses.init_pair(42, curses.COLOR_WHITE, curses.COLOR_WHITE)
        #self.stdscr.bkgd(' ', curses.color_pair(42))
        self.stdscr.refresh()

    def __update_window_size(self):
        self.maxy, self.maxx = self.stdscr.getmaxyx()

"""
if __name__ == "__main__":
    Tui().main()
"""
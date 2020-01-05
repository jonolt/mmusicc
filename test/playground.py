
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mmusicc.mmusicc import MusicManager, Metadata


if __name__ == '__main__':
    mm = MusicManager()
    mm.source_path = "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac"
    mm.target_path = "/home/johannes/Desktop/MusicManager/media/Abrahma/Reflections_In_The_Bowels_Of_A_Bird_(2015)/01_Fountains_Of_Vengeance.flac"
    mm._compare_tui()


    #mm.source_path = "/home/johannes/Desktop/MusicManager/media/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac"

    #mm.target_path = "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac"
    #mm._compare_tui()
    #mm.target[0].import_tag(mm.source[0])
    #mm.target[0].write_tag()

    #mm.target_path = "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.mp3"
    #mm.target[0].import_tag(mm.source[0])
    #mm.target[0].write_tag()
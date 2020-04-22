import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    import os.path

    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    import mmusicc

    mmusicc.MmusicC(args)


if __name__ == "__main__":
    main()

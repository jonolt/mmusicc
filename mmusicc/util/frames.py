from mutagen import id3

text_frames = {
    id3.TALB: 'album',
    id3.TBPM: 'bpm',
    id3.TCOM: 'composer',
    id3.TCOP: "copyright",
    id3.TDAT: "date",  # TTMM
    id3.TDLY: "audiodelay",
    id3.TENC: "encodedby",
    id3.TEXT: "lyricist",
    id3.TFLT: "filetype",
    id3.TIME: "time",
    id3.TIT1: "grouping",
    id3.TIT2: "title",
    id3.TIT3: "version",
    id3.TKEY: "initialkey",
    id3.TLAN: "language",
    id3.TLEN: "audiolength",
    id3.TMED: "mediatype",
    id3.TMOO: "mood",
    id3.TOAL: "originalalbum",
    id3.TOFN: "filename",
    id3.TOLY: "author",
    id3.TOPE: "originalartist",
    id3.TORY: "originalyear",
    id3.TOWN: "fileowner",
    id3.TPE1: "artist",
    id3.TPE2: "albumartist",
    id3.TPE3: "conductor",
    id3.TPE4: "arranger",
    id3.TPOS: "discnumber",
    id3.TPRO: "producednotice",
    id3.TPUB: "organization",
    id3.TRCK: "track",
    id3.TRDA: "recordingdates",
    id3.TRSN: "radiostationname",
    id3.TRSO: "radioowner",
    id3.TSIZ: "audiosize",
    id3.TSOA: "albumsortorder",
    id3.TSOP: "performersortorder",
    id3.TSOT: "titlesortorder",
    id3.TSRC: "isrc",
    id3.TSSE: "encodingsettings",
    id3.TSST: "setsubtitle",
    id3.TYER: 'year'}  # YYYY

time_frames = {
    id3.TDEN: "encodingtime",
    id3.TDOR: "originalreleasetime",
    id3.TDRC: "year",
    id3.TDRL: "releasetime",
    id3.TDTG: "taggingtime"}

paired_textframes = {
    id3.TIPL: "involvedpeople",
    id3.TMCL: "musiciancredits",
    id3.IPLS: "involvedpeople"}

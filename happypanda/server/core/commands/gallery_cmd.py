from happypanda.common import utils, hlogger
from happypanda.server.core.command import Command, UndoCommand, CommandEvent, CommandEntry
from happypanda.server.core import db


log = hlogger.Logger(__name__)

class GalleryRename(UndoCommand):
    """
    Rename a gallery
    """

    renamed = CommandEvent("renamed", str)
    rename = CommandEntry("rename", None, str, str)

    def __init__(self):
        super().__init__()
        self.title = None
        self.old_title = None

    def main(self, title: db.Title, new_title: str) -> None:

        self.title = title
        self.old_title = title.name

        with self.rename.call(title.name, new_title) as plg:
            title.name = plg.first()

            with utils.session() as s:
                s.add(title)

        self.renamed.emit(title.name)
            
    def undo(self):
        self.title.name = self.old_title

        with utils.session() as s:
            s.add(self.title)

        self.renamed.emit(self.old_title)

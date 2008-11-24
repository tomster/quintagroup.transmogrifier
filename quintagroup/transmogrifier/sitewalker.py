from zope.interface import classProvides, implements
from zope.annotation.interfaces import IAnnotations

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint

from Products.CMFCore.interfaces import IFolderish
from Products.Archetypes.interfaces import IBaseFolder

from quintagroup.transmogrifier.logger import VALIDATIONKEY

class SiteWalkerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.pathkey = options.get('path-key', '_path').strip()
        self.typekey = options.get('type-key', '_type').strip()
        self.entrieskey = options.get('entries-key', '_entries').strip()
        # this is used for communication with 'logger' section
        self.anno = IAnnotations(transmogrifier)
        self.storage = self.anno.setdefault(VALIDATIONKEY, [])

    def walk(self, obj):
        if IFolderish.providedBy(obj) or IBaseFolder.providedBy(obj):
            contained = [(k, v.getPortalTypeName()) for k, v in obj.contentItems()]
            yield obj, tuple(contained)
            for v in obj.contentValues():
                for x in self.walk(v):
                    yield x
        else:
            yield obj, ()

    def __iter__(self):
        for item in self.previous:
            yield item

        for obj, contained in self.walk(self.context):
            item = {
                self.pathkey: '/'.join(obj.getPhysicalPath()[2:]),
                self.typekey: obj.getPortalTypeName(),
            }
            if contained:
                item[self.entrieskey] = contained
            # add item path to stack
            self.storage.append(item[self.pathkey])
        
            yield item

        # cleanup
        if VALIDATIONKEY in self.anno:
            del self.anno[VALIDATIONKEY]

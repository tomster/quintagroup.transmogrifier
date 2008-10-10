from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint

from Products.CMFCore.interfaces import IFolderish
from Products.Archetypes.interfaces import IBaseFolder

class SiteWalkerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

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
                '_path': '/'.join(obj.getPhysicalPath()[2:]),
                '_type': obj.getPortalTypeName(),
            }
            if contained:
                item['_entries'] = contained
            yield item


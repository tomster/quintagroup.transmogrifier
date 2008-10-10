from zope.interface import classProvides, implements
from ZODB.POSException import ConflictError

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

from Products.Marshall import registry
from Products.Archetypes.interfaces import IBaseObject

class MarshallSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.excludekey = defaultMatcher(options, 'exclude-key', name, 'excluded_fields')

        self.marshaller = registry.getComponent("atxml")

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            if not pathkey:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if IBaseObject.providedBy(obj):
                excludekey = self.excludekey(*item.keys())[0]
                atns_exclude = ()
                if excludekey:
                    atns_exclude = item[excludekey]
                    
                try:
                    content_type, length, data = self.marshaller.marshall(obj, atns_exclude=atns_exclude)
                except ConflictError:
                    raise
                except:
                    data = None
                    
                if data or data is None:
                    # None value has special meaning for IExportDataCorrector adapter for topic criterias
                    files = item.setdefault('_files', {})
                    item['_files']['marshall'] = {
                        'name': '.marshall.xml',
                        'data': data,
                    }

            yield item

from xml.dom import minidom

from zope.interface import classProvides, implements
from zope.component import queryAdapter

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

from quintagroup.transmogrifier.interfaces import IExportDataCorrector

class ExportAdaptersSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.datakey = defaultMatcher(options, 'data-key', name, 'data')

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            datakey = self.datakey(*item.keys())[0]

            if not (pathkey and datakey):
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            data_store = item[datakey]
            if not data_store:
                yield item; continue

            for name, data in data_store.items():
                adapter = queryAdapter(obj, IExportDataCorrector, name)
                if adapter:
                    data_store[name] = adapter(data)

            yield item

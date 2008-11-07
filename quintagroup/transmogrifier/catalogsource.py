from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint

from Products.CMFCore import utils

class CatalogSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = options.pop('path-key', '_path')
        self.entrieskey = options.pop('entries-key', '_entries')

        # remove 'blueprint' option - it cannot be a query
        options.pop('blueprint')

        self.query = {}
        for k, v in options.items():
            for p in v.split(';'):
                params = p.split('=', 1)
                if len(params) == 1:
                    self.query[k] = p.strip()
                else :
                    q = self.query.setdefault(k, {})
                    q[params[0].strip()] = params[1].strip()

        self.catalog = utils.getToolByName(self.context, 'portal_catalog')

    def __iter__(self):
        for item in self.previous:
            yield item

        for brain in self.catalog(**self.query):
            path = brain.getPath()
            # path == '/plone/folder'
            container_path = path[:path.rfind('/')]
            # container_path == '/plone'
            contained = self.getContained(container_path)
            if contained:
                yield {
                    '_path': '/'.join(path.split('/')[2:-1]),
                    '_entries': contained,
                }
            item = {
                '_path': '/'.join(path.split('/')[2:]),
            }
            yield item

    def getContained(self, path):
        """ path is '/plone/folder'
        """
        # check if this is right
        results = []
        raw_results = self.catalog(path=path, **self.query)
        for brain in raw_results:
            current = brain.getPath()
            relative = current[len(path):]
            relative = relative.strip('/')
            if not relative or '/' in relative:
                continue
            results.append(brain)
        contained = [(i.getId, str(i.Type)) for i in results]
        return tuple(contained)

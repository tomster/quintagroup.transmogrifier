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

        exported = []

        results = list(self.catalog(**self.query))
        results.sort(key=lambda x: x.getPath())
        for brain in results:
            # discussion items are get catalogued too
            # we need to skip them
            if brain.Type == 'Discussion Item':
                continue

            path = brain.getPath()

            # folderish objects are tried to export twice:
            # when their contained items are exported and when they are
            # returned in catalog search results
            if path in exported:
                continue
            exported.append(path)

            container_path = path.rsplit('/', 1)[0]
            contained = self.getContained(container_path)
            if contained and container_path not in exported:
                exported.append(container_path)
                yield {
                    self.pathkey: '/'.join(path.split('/')[2:-1]),
                    self.entrieskey: contained,
                }
            item = {
                self.pathkey: '/'.join(path.split('/')[2:]),
            }
            if brain.is_folderish:
                contained = self.getContained(path)
                if contained:
                    item[self.entrieskey] = contained

            yield item

    def getContained(self, path):
        """ Return list of (object_id, portal_type) for objects that are returned by catalog
            and contained in folder with given 'path'.
        """
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

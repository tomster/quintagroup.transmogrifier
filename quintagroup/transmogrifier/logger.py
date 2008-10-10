import logging

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher

class LoggerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        keys = options.get('keys') or ''
        self.keys = Matcher(*keys.splitlines())
        self.previous = previous
        self.logger = name

    def __iter__(self):
        for item in self.previous:
            items = []
            for key in item.keys():
                if self.keys(key)[0] is not None:
                    items.append("%s=%s" % (key, item[key]))
            if items:
                msg = ", ".join(items)
                logging.getLogger(self.logger).info(msg)
            yield item

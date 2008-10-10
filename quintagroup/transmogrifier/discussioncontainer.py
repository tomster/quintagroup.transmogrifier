from xml.dom import minidom

from zope.interface import classProvides, implements

from Acquisition import aq_base

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

class DiscussionContainerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')

        self.doc = minidom.Document()


    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            if not pathkey:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            # check if object has comments
            discussion_container = getattr(aq_base(obj), 'talkback', None)
            if discussion_container is not None:
                data = self.extractComments(discussion_container)
                if data:
                    files = item.setdefault('_files', {})
                    item['_files']['discussioncontainer'] = {
                        'name': '.comments.xml',
                        'data': data,
                    }

            yield item

    def extractComments(self, container):
        doc = self.doc

        items = container.objectItems()
        if not items:
            return None

        root = doc.createElement('discussion')
        doc.appendChild(root)
        for item_id, item in items:
            hdrlist = item.getMetadataHeaders()
            # get creator (it is displayed in "Posted by")
            hdrlist.append(('Creator', item.Creator()))
            # get modification date (also is displayed)
            hdrlist.append(('Modification_date', item.ModificationDate()))
            # get relation
            hdrlist.append(('In_reply_to', str(item.in_reply_to)))
            # get comment text
            hdrlist.append(('Text', item.text))

            item_elem = doc.createElement('item')
            attr = doc.createAttribute('id')
            attr.value = item_id
            item_elem.setAttributeNode(attr)

            for k, v in hdrlist:
                field = doc.createElement('field')
                attr = doc.createAttribute('name')
                attr.value = k
                field.setAttributeNode(attr)
                text = doc.createTextNode(v)
                field.appendChild(text)
                item_elem.appendChild(field)

            root.appendChild(item_elem)

        # all comments are strings encoded in 'utf-8' and they will properly
        # saved in xml file, but if we explicitly give 'utf-8' encoding
        # UnicodeDecodeError will be raised when they have non-ascii chars
        data = self.doc.toprettyxml(indent='  ') #, encoding='utf-8')

        self.doc.unlink()
        return data

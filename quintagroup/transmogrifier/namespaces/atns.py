"""
    Archetypes Marshall namespace but which can safely handle
    Control Characters for you
"""

from Products.Archetypes.interfaces import IBaseUnit
from Products.Archetypes.interfaces import IObjectField

from Products.Marshall import config
from Products.Marshall.handlers.atxml import XmlNamespace
from Products.Marshall.handlers.atxml import SchemaAttribute
from Products.Marshall.handlers.atxml import getRegisteredNamespaces
from Products.Marshall.exceptions import MarshallingException
from Products.Marshall import utils

from Products.Marshall.namespaces import atns as base

from quintagroup.transmogrifier.namespaces.util import has_ctrlchars


class ATAttribute(base.ATAttribute):


    def serialize(self, dom, parent_node, instance, options={}):
        
        values = self.get(instance)
        if not values:
            return

        is_ref = self.isReference(instance)
        
        for value in values:
            node = dom.createElementNS(self.namespace.xmlns, "field")
            name_attr = dom.createAttribute("name")
            name_attr.value = self.name
            node.setAttributeNode(name_attr)
            
            # try to get 'utf-8' encoded string
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif IBaseUnit.providedBy(value):
                value = value.getRaw(encoding='utf-8')
            else:
                value = str(value)

            if is_ref:
                if config.HANDLE_REFS:
                    ref_node = dom.createElementNS(self.namespace.xmlns,
                                                    'reference')
                    uid_node = dom.createElementNS(self.namespace.xmlns,
                                                    'uid')
                    value = dom.createTextNode(value)
                    uid_node.append(value)
                    ref_node.append(uid_node)
                    node.append(ref_node)
            elif isinstance(value, str) and has_ctrlchars(value):
                value = value.encode('base64')
                attr = dom.createAttributeNS(self.namespace.xmlns,
                                             'transfer_encoding')
                attr.value = 'base64'
                node.setAttributeNode(attr)
                value_node = dom.createCDATASection(value)
                node.appendChild(value_node)
            else:
                value_node = dom.createTextNode(value)
                node.appendChild(value_node)

            field = instance.schema._fields[self.name]
            if IObjectField.providedBy(field):
                mime_attr = dom.createAttribute('mimetype')
                mime_attr.value = field.getContentType(instance)
                node.setAttributeNode(mime_attr)
        
            node.normalize()
            parent_node.appendChild(node)

        return True

    def processXmlValue(self, context, value):
        if value is None:
            return

        value = value.strip()
        if not value:
            return

        # decode node value if needed
        te = context.node.get('transfer_encoding', None)
        if te is not None:
            value = value.decode(te)

        data = context.getDataFor(self.namespace.xmlns)
        if data.has_key(self.name):
            svalues = data[self.name]
            if not isinstance(svalues, list):
                data[self.name] = svalues = [svalues]
            svalues.append(value)
            return
        else:
            data[self.name] = value

class Archetypes(base.Archetypes):

    def getAttributeByName(self, schema_name, context=None):
        if context is not None and schema_name not in self.at_fields:
            if not context.instance.Schema().has_key(schema_name):
                return
                raise AssertionError, \
                      "invalid attribute %s"%(schema_name)
        
        if schema_name in self.at_fields:
            return self.at_fields[schema_name]

        attribute = ATAttribute(schema_name)
        attribute.setNamespace(self)
        
        return attribute

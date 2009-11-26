"""
    CMF Marshall namespace is overrided here in order to fix
    LocalRolesAttribute class. It's not working in Marshall Product.
"""

from Products.Marshall import utils
from Products.Marshall.namespaces import cmfns as base


class LocalRolesAttribute(base.LocalRolesAttribute):

    def getAttributeNames(self):
        return (self.name, 'security')
    
    def processXml(self, context, node):
        tag, namespace = utils.fixtag(node.tag,context.ns_map)
        nsprefix = node.tag[:node.tag.find('}')+1]
        local_roles = node.findall(nsprefix+self.name)
        
        if len(local_roles) == 0:
            return

        data = context.getDataFor(self.namespace.xmlns)
        values = data.setdefault(self.name, [])
        
        for lrole in local_roles:
            values.append((lrole.get('user_id'), lrole.get('role')))
        
        return True
    
class CMF(base.CMF):
    
    attributes = (
        base.TypeAttribute('type'),
        base.WorkflowAttribute('workflow_history '),
        LocalRolesAttribute('local_role')
        )

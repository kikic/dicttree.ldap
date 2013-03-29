import ldap

from ldap import SCOPE_BASE
from ldap import NO_SUCH_OBJECT

import ipdb

class Attributes(object):
    def __init__(self, dn=None, attrs=(), ldap=None):
        self.dn = dn
        self.attrs = attrs
        self._ldap = ldap

    def __contains__(self, name):
        entry = self._ldap.search_s(self.dn, SCOPE_BASE,
                                    attrlist=[name], attrsonly=True)[0]
        return len(entry[1]) > 0

    def __getitem__(self, name):
        entry = self._ldap.search_s(self.dn, SCOPE_BASE,
                                    attrlist=[name])[0]
        return entry[1][name]

    def __setitem__(self, name, value):
        action = ldap.MOD_ADD
        if name in self:
            action = ldap.MOD_REPLACE
        self._ldap.modify_s(self.dn, [(action, name, value)])

    def __delitem__(self, name, value=None):
        """ delete attibutes value, if value is None
        deletes all values for given attribute name """
        self._ldap.modify_s(self.dn, [(ldap.MOD_DELETE, name, value)])

    def __iter__(self):
        return (name for name in self._search(self.dn, SCOPE_BASE))

    def _search(self, base, scope, filterstr='(objectClass=*)', attrlist=None,
                timeout=-1):
        """ldap search returning a generator on attributes
        """
        entry = self._ldap.search_s(base, scope,
                                  filterstr=filterstr, attrlist=attrlist)
        for name in entry[0][1]:
            yield name

    def __len__(self):
        return sum(1 for x in iter(self))

    def __eq__(self, other):
        # XXX quick fix, for old test cases
        return self.items() == dict(other.attrs).items()

    def items(self):
        # XXX quick fix, for old test cases
        return dict(self.attrs).items()



class Node(object):
    def __init__(self, name=None, attrs=(), ldap=None):
        self.name = name
        # python-ldap uses (unordered) dicts to return attributes. I
        # am under the impression that openldap preserves attribute
        # order from an ldif file, which would mean patching
        # python-ldap would give us order. Needs to be investigated.
        #self.attrs = OrderedDict(attrs)
        #self.attrs = dict(attrs)
        self.attrs = Attributes(dn=name, attrs=attrs, ldap=ldap)
        self._ldap = ldap

    def __eq__(self, other):
        return self is other or \
            self.name == other.name and \
            self.attrs == other.attrs

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<ldap node dn="%s">' % (self.name,)

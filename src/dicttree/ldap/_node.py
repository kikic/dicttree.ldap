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

    def __iter__(self):
        return (name for name in self._search(self.dn, SCOPE_BASE))

    def _search(self, base, scope, filterstr='(objectClass=*)', attrlist=None,
                timeout=-1):
        """asynchronous ldap search returning a generator
        """
        msgid = self._ldap.search(base, scope,
                                  filterstr=filterstr, attrlist=attrlist)
        rtype = ldap.RES_SEARCH_ENTRY
        while rtype is ldap.RES_SEARCH_ENTRY:
            # Fetch results single file, the final result (usually)
            # has an empty field. <sigh>
            (rtype, data) = self._ldap.result(msgid=msgid, all=0,
                                              timeout=timeout)
            if rtype is ldap.RES_SEARCH_ENTRY or data:
                for name in data[0][1]:
                    yield name


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

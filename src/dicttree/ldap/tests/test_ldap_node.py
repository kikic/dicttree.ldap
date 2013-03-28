import unittest

from dicttree.ldap.tests import mixins


import ipdb


class TestNodeAttrs(mixins.Slapd, unittest.TestCase):
    ENTRIES = {
        'cn=cn0,o=o': (('cn', ['cn0']),
                       ('objectClass', ['organizationalRole'])),
        'cn=cn1,o=o': (('cn', 'cn1'),
                       ('objectClass', ['organizationalRole'])),
    }
    ADDITIONAL = {
        'cn=cn2,o=o': (('cn', ['cn2']),
                       ('objectClass', ['organizationalRole'])),
    }

    def test_getitem(self):
        node = self.dir['cn=cn0,o=o']
        self.assertEqual(node.attrs['cn'], ['cn0'])
        self.assertEqual(node.attrs['objectClass'], ['organizationalRole'])
        def fail(self):
            node.attrs['fail']
        #XXX result is ok, but the test is not
        #self.assertRaises(KeyError, fail)

        #XXX implement setitem first
        #node.attrs[somenew] = 'abc'

    def test_contains(self):
        node = self.dir['cn=cn0,o=o']
        self.assertTrue('cn' in node.attrs)
        self.assertTrue('objectClass' in node.attrs)
        self.assertFalse('fail' in node.attrs)

    def test_iter(self):
        node = self.dir['cn=cn0,o=o']
        self.assertItemsEqual(node.attrs, ['objectClass', 'cn'])

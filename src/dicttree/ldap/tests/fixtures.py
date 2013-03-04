import os
import time

from ldap.ldapobject import LDAPObject
from subprocess import Popen, PIPE

from dicttree.ldap.tests.fixture import Fixture


class slapd(Fixture):
    """Manage slapd instance for a group of tests
    """
    @classmethod
    def setUpFixture(fixture):
        """start slapd

        ldap data dir is wiped and a fresh base dn added. In case of
        errors the SLAPD process is supposed to be killed.
        """
        # ensure ldap dirs exist
        datadir = 'var/openldap-data'
        for x in (datadir, 'var/log', 'var/run'):
            if not os.path.exists(x):
                os.makedirs(x)

        # wipe ldap data dir and empty logfile (enable tailf)
        dbfiles = os.listdir(datadir)
        for x in dbfiles:
            os.unlink(datadir + '/' + x)
        with open('var/log/slapd.log', 'w') as f:
            f.truncate(0)

        # start ldap server
        # loglevels for -d
        # 1      (0x1 trace) trace function calls
        # 2      (0x2 packets) debug packet handling
        # 4      (0x4 args) heavy trace debugging (function args)
        # 8      (0x8 conns) connection management
        # 16     (0x10 BER) print out packets sent and received
        # 32     (0x20 filter) search filter processing
        # 64     (0x40 config) configuration file processing
        # 128    (0x80 ACL) access control list processing
        # 256    (0x100 stats) connections, LDAP operations, results (recommended)
        # 512    (0x200 stats2) stats log entries sent
        # 1024   (0x400 shell) print communication with shell backends
        # 2048   (0x800 parse) entry parsing
        fixture.process = Popen(
            ["nixenv/libexec/slapd",
             "-f", "etc/openldap/slapd.conf",
             "-d", "stats",
             "-s", "0",
             "-h", "ldapi://var%2Frun%2Fldapi"], stdout=PIPE, stderr=PIPE)

        # wait for ldap to appear
        waited = 0
        while True:
            try:
                fixture.con = LDAPObject('ldapi://var%2Frun%2Fldapi')
                fixture.con.bind_s('cn=root,o=o', 'secret')
            except:
                if waited > 10:
                    fixture.tearDownFixture()
                    raise
                time.sleep(0.1)
                waited = waited + 1
            else:
                break

        # add base dn
        try:
            fixture.con.add_s('o=o', (('o', 'o'),
                                      ('objectClass', 'organization'),))
        except:
            fixture.tearDownFixture()
            raise

    @classmethod
    def tearDownFixture(fixture):
        """make sure ldap is killed before we return
        """
        fixture.process.kill()
        fixture.process.wait()

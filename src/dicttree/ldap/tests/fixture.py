"""Test fixtures to be shared across modules

unittest provides three layers of test fixtures:
- setUp/tearDown on a TestCase are run for each test of the testcase,
- setUpClass/tearDownClass are run once per TestCase (given that tests
  are grouped per testcase, the default)
- setUpModule/tearDownModule are run once per module (given that
  testcases are grouped by module, the default)

The goal here is to provide fixture setup and tear down once for a
group of tests that can be spread accross modules and organized in
separate hierarchies. Such a fixture is realized as a decorator and
test cases are assigned to a fixture by applying the decorator.

"""

import sys
import traceback


class FixtureMeta(type):
    """metaclass for fixtures

    Keep track of testcases a fixture is applied to.
    """
    def __call__(fixture, testcase):
        """Apply fixture to a testcase

        @fixture
        class Test(TestCase):
            pass

        Add setUpClass/tearDownClass to the testcase. These need to
        execute eventually existing setUpClass/tearDownClass.
        """
        setUpTestCase = getattr(testcase, 'setUpClass', lambda:None)
        tearDownTestCase = getattr(testcase, 'tearDownClass', lambda:None)

        @classmethod
        def setUpClass(testcase):
            if not fixture.setup:
                fixture.setUpFixture()
                fixture.setup = True
            try:
                setUpTestCase()
            except Exception, e:
                sys.stderr.write("""
======================================================================
Error setting up testcase: %s
----------------------------------------------------------------------
%s
""" % (str(e), traceback.format_exc()))

        @classmethod
        def tearDownClass(testcase):
            try:
                tearDownTestCase()
            except:
                sys.stderr.write("""
======================================================================
Error tearing down testcase: %s
----------------------------------------------------------------------
%s
""" % (str(e), traceback.format_exc()))
            fixture.testcases.remove(testcase)
            if len(fixture.testcases) == 0:
                fixture.tearDownFixture()
                fixture.setup = False

        testcase.setUpClass = setUpClass
        testcase.tearDownClass = tearDownClass
        setattr(testcase, fixture.__name__, fixture)
        fixture.testcases.append(testcase)
        return testcase

    def __init__(fixture, name, bases, dct):
        super(FixtureMeta, fixture).__init__(name, bases, dct)
        fixture.testcases = []
        fixture.setup = False


class Fixture(object):
    """base class for fixture decorators
    """
    __metaclass__ = FixtureMeta

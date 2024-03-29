from TestingFramework.Assertions import Assertions


class TestAssertions(Assertions):

    def testList(self):
        self.assertListEqual([1, 1.0, "hello!", None, False], "[1, 1.0, \"hello!\", None, False]")
        self.assertListEqual([1, 1.0, "hello!", None, False], [1, 1.0, "hello!", None, False])

    def testListFailure1(self):
        with self.assertRaises(AssertionError):
            self.assertListEqual([2, 3.0, "Hello!", None, False], [2, 3.0, "Goodbye!", None, False])

    def testListFailure2(self):
        with self.assertRaises(AssertionError):
            self.assertListEqual([2, "Hello!", None], [2, "Hello!"])

    def testListFailure3(self):
        with self.assertRaises(AssertionError):
            self.assertListEqual([2, 2.0], "[2, 2.0, 3.0]")

    def testListAlmostEquals(self):
        self.assertListAlmostEqual([1.001, 1.0021], "[1.002, 1.0011]", .001)
        self.assertListAlmostEqual([1.001], "[1.000]", .001)

    def testListAlmostEqualsFailure(self):
        # this should fail bc that 1.00014 rounds down and 1.0025 rounds up
        with self.assertRaises(AssertionError):
            self.assertListAlmostEqual([1.0025], [1.0014], .001)

    def testTuple(self):
        self.assertTupleEqual((1, 2), (1, 2))

    def testTupleFailure(self):
        with self.assertRaises(AssertionError):
            self.assertTupleEqual((1, 1), (1, 2))

    def testAlmostEquals(self):
        self.assertAlmostEquals(1, 0.8, _delta=.2)

    def testAlmostEqualsFailure(self):
        with self.assertRaises(AssertionError):
            self.assertAlmostEquals(1, 1.3, _delta=.2)

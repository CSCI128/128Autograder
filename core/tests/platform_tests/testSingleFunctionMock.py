import unittest
from autograder_platform.TestingFramework.SingleFunctionMock import SingleFunctionMock


class TestSingleFunctionMock(unittest.TestCase):

    def testSideEffect(self):
        funcToMock = SingleFunctionMock("funcToMock", ["goodbye"])  # type: ignore

        self.assertEqual("goodbye", funcToMock())

    def testSideEffectManyCalls(self):
        sideEffects = [1, 2, 3, 4, 5]

        funcToMock = SingleFunctionMock("funcToMock", sideEffects)  # type: ignore

        actual = []
        for _ in range(10):
            actual.append(funcToMock())

        sideEffects.extend([5, 5, 5, 5, 5])

        self.assertEqual(sideEffects, actual)

    def testVoidSideEffectManyCalls(self):
        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        self.assertIsNone(funcToMock())

    def testCalled(self):
        def funcToMock():
            return "hello"

        funcToMock()

        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        funcToMock()

        funcToMock.assertCalledTimes(1)

    def testCalledFailure(self):
        def funcToMock():
            return "hello"

        funcToMock()

        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        with self.assertRaises(AssertionError):
            funcToMock.assertCalledTimes(1)

        with self.assertRaises(AssertionError):
            funcToMock.assertCalled()

        funcToMock.assertNotCalled()



    def testCalledWith(self):
        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        funcToMock(1, 2, 3)

        funcToMock.assertCalledWith(1, 2, 3)

    def testCalledWithFailure(self):
        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        funcToMock(1, 2)

        with self.assertRaises(AssertionError):
            funcToMock.assertCalledWith(1, 2, 3)

    def testCalledWithManyCalls(self):
        funcToMock = SingleFunctionMock("funcToMock", None)  # type: ignore

        for i in range(10):
            funcToMock(i, i, i)

        funcToMock.assertCalledWith(3, 3, 3)

    def testCalledWithSpy(self):
        def funcToMock(a, b, c):
            return a + b + c

        funcToMockSrc = funcToMock
        funcToMock = SingleFunctionMock("funcToMock", spy=True)

        funcToMock.setSpyFunction(funcToMockSrc)

        result = funcToMock(1, 2, 3)

        self.assertEqual(6, result)
        funcToMock.assertCalledTimes(1)

    def testCalledWithKwargs(self):
        funToMock = SingleFunctionMock("funcToMock", None)

        funToMock(1, 2, 3, a=1, b=2, c=3)

        funToMock.assertCalledWith(1, 2, 3, a=1, b=2, c=3)

    def testCalledWithKwargsFailure(self):
        funToMock = SingleFunctionMock("funcToMock", None)

        funToMock(1, 2, 3, a=1, b=2)

        with self.assertRaises(AssertionError):
            funToMock.assertCalledWith(1, 2, 3, a=1, b=2, c=3)

    def testCalledAtLeast(self):
        funcToMock = SingleFunctionMock("funcToMock", None)

        for _ in range(5):
            funcToMock()

        funcToMock.assertCalledAtLeastTimes(4)

    def testCalledAtLeastFailure(self):
        funcToMock = SingleFunctionMock("funcToMock", None)

        for _ in range(5):
            funcToMock()

        with self.assertRaises(AssertionError):
            funcToMock.assertCalledAtLeastTimes(6)

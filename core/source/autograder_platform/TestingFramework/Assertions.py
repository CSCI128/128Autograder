import math
import re
import unittest
from typing import Optional, List, Any


class Assertions(unittest.TestCase):
    """
    This class contains the base assertions for the autograder platform. It overrides the one in the base TestCase class

    The primary differentiation factor of this is that it formats the outputs in a nicer way for both gradescope and the
    local autograder
    """
    def __init__(self, testResults):
        super().__init__(testResults)
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)
        # self.addTypeEqualityFunc(dict, self.assertDictEqual)
        self.addTypeEqualityFunc(list, self.assertListEqual)
        self.addTypeEqualityFunc(tuple, self.assertTupleEqual)

    @staticmethod
    def _stripOutput(outputLine: str) -> str:
        if not isinstance(outputLine, str):
            raise AssertionError(f"Expected a string. Got {type(outputLine).__qualname__}")

        if "output " in outputLine.lower():
            outputLine = outputLine[7:]

        outputLine = outputLine.strip()

        return outputLine

    @staticmethod
    def _convertStringToList(outputLine: str) -> list[str]:
        if not isinstance(outputLine, str):
            raise AssertionError(f"Expected a string. Got {type(outputLine).__qualname__}")

        outputLine = Assertions._stripOutput(outputLine)

        if "[" in outputLine:
            outputLine = outputLine[1:]
        if "]" in outputLine:
            outputLine = outputLine[:-1]
        outputLine = outputLine.strip()

        parsedList: list[str] = outputLine.split(",")
        charsToRemove = re.compile("[\"']")
        parsedList = [el.strip() for el in parsedList]
        parsedList = [re.sub(charsToRemove, "", el) for el in parsedList]
        return parsedList

    @staticmethod
    def _raiseFailure(shortDescription: str, expectedObject: object, actualObject: object, msg: Optional[str]):
        errorMsg = f"Incorrect {shortDescription}.\n" + \
                   f"Expected {shortDescription}: {expectedObject}\n" + \
                   f"Your {shortDescription}    : {actualObject}"
        if msg:
            errorMsg += "\n\n" + str(msg)

        raise AssertionError(errorMsg)

    @staticmethod
    def _convertIterableFromString(expected, actual):
        for i in range(len(expected)):
            parsedActual = object
            expectedType = type(expected[i])
            try:
                if isinstance(actual[i], type(expected[i])):
                    parsedActual = actual[i]
                elif expected[i] is None:
                    if actual[i] == "None":
                        parsedActual = None
                elif isinstance(expected[i], bool):
                    parsedActual = True if actual[i] == "True" else False
                else:
                    parsedActual = expectedType(actual[i])
            except Exception:
                raise AssertionError(f"Failed to parse {expectedType.__qualname__} from {actual[i]}")

            actual[i] = parsedActual

        return actual

    def _assertIterableEqual(self, expected, actual, msg: Optional[str] = None):
        for i in range(len(expected)):
            if expected[i] != actual[i]:
                self._raiseFailure("output", expected[i], actual[i], msg)

    @staticmethod
    def findPrecision(x: float):
        """
        This function is stolen from stack overflow verbatim - it computes the precision of a float
        """
        max_digits = 14
        int_part = int(abs(x))
        magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
        if magnitude >= max_digits:
            return magnitude
        frac_part = abs(x) - int_part
        multiplier = 10 ** (max_digits - magnitude)
        frac_digits = multiplier + int(multiplier * frac_part + 0.5)
        while frac_digits % 10 == 0:
            frac_digits /= 10
        scale = int(math.log10(frac_digits))
        return magnitude + scale

    def assertMultiLineEqual(self, expected: str, actual: str, msg: Optional[str] = None) -> None:
        if not isinstance(expected, str):
            raise AttributeError(f"Expected must be string. Actually is {type(expected).__qualname__}")
        if not isinstance(actual, str):
            raise AssertionError(f"Expected a string. Got {type(actual).__qualname__}")

        if expected != actual:
            self._raiseFailure("output", expected, actual, msg)

    def _assertListPreCheck(self, expected: list[any], actual: list[object] | str, msg: Optional[str] = None):
        if not isinstance(expected, list):
            raise AttributeError(f"Expected must be a list. Actually is {type(expected).__qualname__}")
        if isinstance(actual, str):
            actual = self._convertStringToList(actual)

        if not isinstance(actual, list):
            raise AssertionError(f"Expected a list. Got {type(actual).__qualname__}")

        if len(expected) != len(actual):
            self._raiseFailure("number of elements", len(expected), len(actual), msg)

        return self._convertIterableFromString(expected, actual)

    def assertListEqual(self, expected: list[any], actual: list[object] | str, msg: Optional[str] = None) -> None:
        actual = self._assertListPreCheck(expected, actual, msg)
        self._assertIterableEqual(expected, actual, msg)

    def assertListAlmostEqual(self, expected: list[any], actual: list[object] | str, allowedDelta: float,
                              msg: Optional[str] = None) -> None:
        actual = self._assertListPreCheck(expected, actual, msg)
        for i in range(len(expected)):
            self.assertAlmostEquals(expected[i], actual[i], delta=allowedDelta)

    def assertTupleEqual(self, expected: tuple[any, ...], actual: tuple[object, ...], msg: Optional[str] = None) -> None:
        if not isinstance(expected, tuple):
            raise AttributeError(f"Expected must be a tuple. Actually is {type(expected).__qualname__}")

        if not isinstance(actual, tuple):
            raise AssertionError(f"Expected a tuple. Got {type(actual).__qualname__}")

        if len(expected) != len(actual):
            self._raiseFailure("number of elements", len(expected), len(actual), msg)

        self._assertIterableEqual(expected, actual, msg)

    def assertDictEqual(self, expected: dict[any, object], actual: dict[object, object], msg: Optional[str] = None) -> None:
        raise NotImplementedError("Use base assert dict equal")

    def assertAlmostEquals(self, expected: float, actual: float, places: int = ..., msg: Optional[str] = None,
                           delta: float = ...) -> None:
        if places is None:
            raise AttributeError("Use delta not places for assertAlmostEquals")

        if round(abs(expected - actual), self.findPrecision(delta)) > delta:
            self._raiseFailure(f"output (allowed delta +/- {delta})", expected, actual, msg)


    @staticmethod
    def assertCorrectNumberOfOutputLines(expected: List[Any], actual: List[Any]):
        if len(actual) == 0:
            raise AssertionError("No OUTPUT lines found. Check OUTPUT formatting.")

        if len(actual) > len(expected):
            raise AssertionError(f"Too many OUTPUT lines. Check OUTPUT formatting.\n"
                                 f"Expected number of lines: {len(expected)}\n"
                                 f"Actual number of lines  : {len(actual)}")

        if len(actual) < len(expected):
            raise AssertionError(f"Too few OUTPUT lines. Check OUTPUT formatting.\n"
                                 f"Expected number of lines: {len(expected)}\n"
                                 f"Actual number of lines  : {len(actual)}")

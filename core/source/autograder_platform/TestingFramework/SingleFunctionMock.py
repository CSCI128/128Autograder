from typing import Callable, List, TypedDict, Tuple, Dict


class CalledWith(TypedDict):
    """
    This dictionary type stores the parameters that the function was called with
    Stores both kwargs and args
    """
    args: Tuple[object, ...]
    kwargs: Dict[str, object]

class SingleFunctionMock:
    """
    This is a simple static mock interface that allows a single function to be mocked.
    It is also pickleable, which is why the ref:`unittest.mock.Mock` could not be used in this application
    """

    def __init__(self, name: str, sideEffect: List[object] | None = None, spy: bool = False):
        self.calledTimes: int = 0
        self.calledWith: List[CalledWith] = []
        self.mockName: str = name
        self.spyFunction: Callable = self
        self.sideEffect: List[object] | None = sideEffect
        self.spy = spy

    def setSpyFunction(self, initialFunctionName: Callable):
        self.spyFunction = initialFunctionName


    def __call__(self, *args, **kwargs):
        self.calledTimes += 1
        self.calledWith.append({"args": args, "kwargs": kwargs})

        if self.spy:
            return self.spyFunction(*args, **kwargs)

        if self.sideEffect is None:
            return None

        if (self.calledTimes - 1) >= len(self.sideEffect):
            return self.sideEffect[len(self.sideEffect) - 1]

        return self.sideEffect[self.calledTimes - 1]

    def assertCalled(self):
        if self.calledTimes == 0:
            raise AssertionError(f"Function: {self.mockName} was not called.\nExpected to be called")

    def assertNotCalled(self):
        if self.calledTimes != 0:
            raise AssertionError(f"Function: {self.mockName} was called.\nExpected not to be called.")

    def assertCalledWith(self, *args, **kwargs):
        self.assertCalled()
        for calledWith in self.calledWith:
            if calledWith["args"] == args and calledWith["kwargs"] == kwargs:
                return

        raise AssertionError(f"Function: {self.mockName} was not called with arguments: {args} {kwargs}.")

    def assertCalledTimes(self, times: int):
        if times != self.calledTimes:
            raise AssertionError(
                f"Function: {self.mockName} was called {self.calledTimes} times.\nExpected to be called {times} times")

    def assertCalledAtLeastTimes(self, times: int):
        if times > self.calledTimes:
            raise AssertionError(
                f"Function: {self.mockName} was called {self.calledTimes} times.\nExpected to be called at least {times} times")

from typing import overload

class Test:
    @overload
    def test(self, address: str):
        ...

    @overload
    def test(self, one: int, two: int):
        ...

    def test(self, one: int | str | None = None, two: int | None = None, address: int | str | None = None):
        print(one, two)

Test().test("test")
Test().test(1, 2)
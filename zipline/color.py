"""
Copyright 2023-present fretgfr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import colorsys
import re
from typing import Tuple

__all__ = ("Color", "Colour")

COLOR_REGEX = re.compile(
    (
        r"(?P<RGB>(?P<R>\d{1,3})(?:,|\s)+(?P<G>\d{1,3})(?:,?\s?)+(?P<B>\d{1,3}))"
        r"|(?P<HSV>(?P<H>\d{1,3}(?:\.\d)?)(?:,|\s)+(?P<S>\d{1,3}(?:\.\d)?)(?:,|\s)+(?P<V>\d{1,3}(?:\.\d)?))"
        r"|(?P<Hex>(?<!\<)\#(?:[a-f0-9]{6}|[a-f0-9]{3}\b))"
    ),
    re.IGNORECASE,
)


class Color:
    """
    Represents a color for use on Zipline.

    An alias named Colour is also supplied.

    .. container:: operations

        .. describe:: str(x)

            Returns the hex format of the color.

        .. describe:: int(x)

            Returns the raw value of the color.

    Attributes
    ------------
    value: :class:`int`
        The raw integer value of this color.
    """

    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return self.to_hex()

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return self.value == other.value

        return NotImplemented

    def __repr__(self) -> str:
        return f"<Color value={self.value}>"

    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xFF

    @property
    def r(self) -> int:
        return self._get_byte(2)

    @property
    def g(self) -> int:
        return self._get_byte(1)

    @property
    def b(self) -> int:
        return self._get_byte(0)

    def to_hex(self) -> str:
        """Returns this Color in hex format as ``#rrggbb``."""
        return f"#{self.value:0>6x}"

    def to_rgb(self) -> Tuple[int, int, int]:
        """Returns this Color in RGB format as ``(r, g, b)``."""
        return (self.r, self.g, self.b)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        """Construct a Color from given red, green, and blue values."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Color:
        """Construct a Color from an HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def from_str(cls, value: str) -> Color:
        """
        Construct a Color from a given string.

        Supported formats:

        - RGB: ```rgb(rrr, ggg, bbb)```
        - HSV: ``hsv(hh, 0.s, 0.v)``
        - Hex: ``#rrggbb`` or ``#rgb``

        Parameters
        ----------
        value: :class:`str`
            The correctly formatted input string.

        Returns
        -------
        :class:`~zipline.color.Color`
            The resulting Color.

        Raises
        ------
        :class:`ValueError`
            Input string does not match supported formats.
        """
        match_ = COLOR_REGEX.search(value)

        if not match_:
            raise ValueError("input string does not match valid inputs.")

        if match_.group("RGB"):
            return cls.from_rgb(*map(int, map(match_.group, "RGB")))
        if match_.group("HSV"):
            return cls.from_hsv(*map(float, map(match_.group, "HSV")))
        if match_.group("Hex"):
            group = match_["Hex"]
            if len(group) == 4:
                group = "#" + "".join(character * 2 for character in group.removeprefix("#"))

            return cls(int(group.lstrip("#"), 16))

        raise RuntimeError("Unreachable")

    @classmethod
    def default(cls) -> Color:
        """The default color, white."""
        return cls(0xFFFFFF)


Colour = Color

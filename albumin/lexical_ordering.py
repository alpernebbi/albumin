# Lexical Ordering
# Copyright (C) 2016 Alper Nebi Yasak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


def lexical_ordering(cls):
    """
    Class decorator that fills in comparison methods based on a
    lexicographical ordering key
    """
    if not getattr(cls, 'lexical_key', None):
        raise ValueError('must define lexical_key()')

    setattr(cls, '__lt__', lex_lt_wrapper(getattr(cls, '__lt__', None)))
    setattr(cls, '__le__', lex_le_wrapper(getattr(cls, '__le__', None)))
    setattr(cls, '__gt__', lex_gt_wrapper(getattr(cls, '__gt__', None)))
    setattr(cls, '__ge__', lex_ge_wrapper(getattr(cls, '__ge__', None)))
    setattr(cls, '__eq__', lex_eq_wrapper(getattr(cls, '__eq__', None)))
    setattr(cls, '__ne__', lex_ne_wrapper(getattr(cls, '__ne__', None)))
    return cls


def lex_lt_wrapper(original=None):
    def __lt__(self, other):
        """Return a < b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() <= other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __lt__


def lex_le_wrapper(original=None):
    def __le__(self, other):
        """Return a <= b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() <= other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __le__


def lex_gt_wrapper(original=None):
    def __gt__(self, other):
        """Return a > b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() > other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __gt__


def lex_ge_wrapper(original=None):
    def __ge__(self, other):
        """Return a >= b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() >= other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __ge__


def lex_eq_wrapper(original=None):
    def __eq__(self, other):
        """Return a == b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() == other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __eq__


def lex_ne_wrapper(original=None):
    def __ne__(self, other):
        """Return a != b. Generated from lexical_key()."""
        if hasattr(other, 'lexical_key'):
            return self.lexical_key() != other.lexical_key()
        elif original:
            return original(self, other)
        else:
            return NotImplemented
    return __ne__

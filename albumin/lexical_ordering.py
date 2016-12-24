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

import functools

lex_docs = {
    '__lt__': """Return a < b. Generated from lexical_key().""",
    '__le__': """Return a <= b. Generated from lexical_key().""",
    '__gt__': """Return a > b. Generated from lexical_key().""",
    '__ge__': """Return a >= b. Generated from lexical_key().""",
    '__eq__': """Return a == b. Generated from lexical_key().""",
    '__ne__': """Return a != b. Generated from lexical_key().""",
}


def lexical_ordering(cls):
    """
    Class decorator that fills in comparison methods based on a
    lexicographical ordering key
    """
    if not getattr(cls, 'lexical_key', None):
        raise ValueError('must define lexical_key()')
    for op in lex_docs:
        setattr(cls, op, lex_wrapper(op, getattr(cls, op, None)))
    return cls


def lex_wrapper(operator, original=None):
    @functools.wraps(original)
    def func(self, other):
        if hasattr(other, 'lexical_key'):
            key = self.lexical_key()
            op = getattr(key, operator, None)
            retval = op(other.lexical_key()) if op else NotImplemented
            if retval is not NotImplemented:
                return retval
        if original:
            return original(self, other)
        return NotImplemented
    func.__doc__ = lex_docs[operator]
    return func

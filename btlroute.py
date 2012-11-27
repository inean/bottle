#!/usr/bin/env python
# -*- mode:python; tab-width: 2; coding: utf-8 -*-

"""
BtlRoute
"""

from __future__ import absolute_import

__author__  = "Carlos Martín"
__license__ = "See LICENSE for details"
__version__ = "0.12-dev1"

# Import here any required modules.
import re

__all__ = ['FilterMixin', 'Path']

class Filters(object):
    """Singleton class to fetch filters"""

    types = {}

    @staticmethod
    def register(a_type, filter_mixin):
        """Register a converter for the given type"""
        Filters.types[a_type] = filter_mixin

    @staticmethod
    def fetch(a_type):
        """Get a registered filter"""
        return Filters.types[a_type]

    @staticmethod
    def parse(a_type, conf):
        """Return a converter for the given type"""
        return Filters.types[a_type].parse(conf)


class MetaFilter(type):
    """Filter Metaclass"""

    # pylint: disable-msg=W0106
    def __init__(mcs, name, bases, dct):
        type.__init__(mcs, name, bases, dct)
        if name.endswith("Filter"):
            Filters.register(name[:-6].lower(), mcs)
            if hasattr(mcs, "alias"):
                [Filters.register(alias, mcs) for alias in mcs.alias]


#pylint: disable-msg=R0903
class FilterMixin(object):
    """Abstract class to create Filters"""

    __metaclass__ = MetaFilter

    @staticmethod
    def parse(conf):
        """
        Parse 'conf' and return a tuple of filter name, mode, and func
        """
        raise NotImplementedError


#pylint: disable-msg=R0903
class ReFilter(FilterMixin):
    """Regular expression based filter"""

    alias = ["default",]

    @staticmethod
    def parse(conf):
        return conf or '[^/]+', None

#pylint: disable-msg=R0903
class IntFilter(FilterMixin):
    """Integer filter"""

    @staticmethod
    def parse(conf):
        return r'-?\d+', int

#pylint: disable-msg=R0903
class FloatFilter(FilterMixin):
    """Float based filter"""

    @staticmethod
    def parse(conf):
        return r'-?[\d.]+', float

#pylint: disable-msg=R0903
class PathFilter(FilterMixin):
    """Path filter"""

    @staticmethod
    def parse(conf):
        return r'.+?', None


class RuleSyntaxError(Exception):
    """
    Simple exception to be fired when an invalid route has been
    declared
    """

class RouteNotFoundError(Exception):
    """Raised when rule doesn't match path"""

class RouteBadFilterError(Exception):
    """Bad filter"""
    
class Rule(object):
    """BottlePy route builder"""
    
    rule_syntax = re.compile(                             \
        '(\\\\*)'                                         \
        '(?:(?::([a-zA-Z_][a-zA-Z_0-9]*)?()(?:#(.*?)#)?)' \
        '|(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)'  \
        '(?::((?:\\\\.|[^\\\\>]+)+)?)?)?>))')

    @classmethod
    def _eval(cls, rule):
        ''' Parses a rule into a (name, filter, conf) token stream. If mode is
            None, name contains a static rule part. '''
        offset, prefix = 0, ''
        for match in cls.rule_syntax.finditer(rule):
            prefix += rule[offset:match.start()]
            #pylint:disable-msg=C0103
            g = match.groups()
            if len(g[0])%2: # Escaped wildcard
                prefix += match.group(0)[len(g[0]):]
                offset = match.end()
                continue
            #pylint:disable-msg=C0321
            if prefix: yield prefix, None, None
            name, filtr, conf = g[1:4] if not g[2] is None else g[4:7]
            filtr = filtr or "default"
            yield name, filtr, conf or None
            offset, prefix = match.end(), ''
        if offset <= len(rule) or prefix:
            yield prefix+rule[offset:], None, None

    #pylint:disable-msg=C0103
    @classmethod
    def process_rule(cls, rule):
        """Get a valid name and regex for a rule"""
        def subs(m):
            """Group selector"""
            return m.group(0) if len(m.group(1)) % 2 else m.group(1) + '(?:'
        def process_key(key, mode, conf):
            """Get a valid regex for key and mode"""
            if mode:
                mask = Filters.parse(mode, conf)[0]
                return '(?P<%s>%s)' % (key, mask) if key else '(?:%s)' % mask
            if key:
                return re.escape(key)
            # catch all
            return ''
        # evaluate rule
        is_static, pattern, filters = True, '', {}
        for key, mode, conf in cls._eval(rule):
            pattern   += process_key(key, mode, conf)
            is_static  = is_static and mode
            #pylint: disable-msg = W0106, C0301
            key and mode and filters.setdefault(key, Filters.parse(mode, conf)[1])
        # if is a dinamic one, calculate a valid name and a valid regex
        name, regex = rule, rule
        if not is_static:
            try:
                name  = re.sub(r'(\\*)(\(\?P<[^>]*>|\((?!\?))', subs, pattern)
                regex = '^(%s)$' % pattern
                _     = re.compile(name).match
            except re.error, ex:
                error = "Bad Route: %s (%s)" % (rule, ex.message)
                raise RuleSyntaxError(error)
        # return name and a valid regex for pattern
        return [name, regex, filters]

#pylint: disable-msg=C0103
class Path(object):
    """The `Route` decorator"""

    #pylint: disable-msg=W0212
    def __init__(self, rule):
        self._rule = rule
        self._pattern = Rule.process_rule(self._rule)

    def __repr__(self):
        return "<%s>" % self.pattern

    def __eq__(self, other):
        return self.name == other.name
        
    @property
    def name(self):
        """Route name"""
        return self._pattern[0]

    @property
    def pattern(self):
        """Full pattern route"""
        return self._pattern[1]

    @property
    def filters(self):
        """Return filters to convert from path"""
        return self._pattern[2]
        
    def match(self, path):
        """Get a collection of valid matches"""
        #pylint: disable-msg=W0201
        if not hasattr(self, '_match_regex'):
            self._match_regex = re.compile(self.pattern)
        # get match
        match = self._match_regex.match(path)
        # raise error when fail
        if match is None:
            raise RouteNotFoundError(self.name, path)
        # parse parameters
        args = match.groupdict()
        for name, wfilter in self.filters.iteritems():
            try:
                if wfilter is not None:
                    args[name] = wfilter(args[name])
            except ValueError, err:
                raise RouteBadFilterError(err.message)
        return args


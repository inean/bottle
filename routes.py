#!/usr/bin/env python
# -*- mode:python; tab-width: 2; coding: utf-8 -*-

"""
Routes
"""

from __future__ import absolute_import

__author__  = "Carlos Martín"
__license__ = "See LICENSE for details"

# Import here any required modules.
import sys
import re
import itertools

__all__ = ['Route', 'route']


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
            in_filter  = key and mode
            in_filter and filters.setdefault(key, Filters.parse(mode, conf)[1])
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
            except ValueError:
                err = 'Wrong format for ' + name + '(' + value + ')'
                raise RouteFilterError(err)
        return args
        
# Tornado Stuff
import tornado.web

class TornadoRoute(Path):
    """Route Singleton"""

    _routes = []

    @classmethod
    def add(cls, handler):
        """Add route to available routes"""
        iterable = itertools.imap(lambda x: x == route, cls._routes)
        if not handler.override and any(iterable):
            return
        cls._routes.append(handler)

    @staticmethod
    def reset(application):
        """Reset application handlers"""
        application.handlers = []
        application.named_handlers = {}

    @classmethod
    def merge(cls, application):
        """Add routes to the `tornado.web.Application`"""
        hosts = {}
        for host, handler in application.handlers:
            hosts[host.pattern] = handler
        for rule in cls._routes:
            hosts.setdefault(rule.host, []).append(rule.spec)
        # now merge hosts
        cls.reset(application)
        for host, spec in hosts.iteritems():
            application.add_handlers(host, spec)
        return application

        
#pylint: disable-msg=C0103
class route(Path):
    """The `Route` decorator"""

    #pylint: disable-msg=W0212
    def __init__(self, rule, initialize=None, host=".*$", override=True):
        super(route, self).__init__(rule)
        self._host     = host
        self._method   = None
        self._override = override
        self._args     = initialize or {}

        # If it's decorating a method, we need to set 'handler's name'
        self._handler  = sys._getframe(1).f_code.co_name

    def __call__(self, handler):
        try:
            # func_name will fail if route is used as class
            # decorator. If so, store handler class name and set
            # method to GET
            self._method = handler.func_name.upper()
        except AttributeError:
            self._handler = handler.__name__
            self._method  = 'GET'
        # store in route collections
        TornadoRoute.add(self)
        return handler

    def __repr__(self):
        return "%s: <%s,%s> (%s)" % \
            (self._host, self._rule, self._pattern, self._handler)

    @property
    def host(self):
        """Route associated host"""
        return self._host

    @property
    def handler(self):
        """Class associated to this route"""
        return self._handler

    @property
    def method(self):
        """Verb associated to this route"""
        return self._method

    @property
    def spec(self):
        """A tornado spec which defiles this route"""
        return tornado.web.URLSpec(self._pattern,
                                   eval(self._handler),
                                   self._args,
                                   ".".join((self._handler, self._method)))

    @property
    def override(self):
        """
        True if this route only should be considered if no one hasb
        been previously defined for this path
        """
        return self._override


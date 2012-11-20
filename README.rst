================================================================================
Routing
================================================================================

BtlRoute uses THE SAME powerful routing engine that bottlePy used to find the right callback for each request. 
This document covers advanced techniques and rule mechanics in detail.

Rule Syntax
--------------------------------------------------------------------------------

The :class:`Path` distinguishes between two basic types of routes: **static routes** (e.g. ``/contact``) and **dynamic routes** (e.g. ``/hello/<name>``). A route that contains one or more *wildcards* it is considered dynamic. All other routes are static.

The simplest form of a wildcard consists of a name enclosed in angle brackets (e.g. ``<name>``). The name should be unique for a given route and form a valid python identifier (alphanumeric, starting with a letter). This is because wildcards are used as keyword arguments for the request callback later.

Each wildcard matches one or more characters, but stops at the first slash (``/``). This equals a regular expression of ``[^/]+`` and ensures that only one path segment is matched and routes with more than one wildcard stay unambiguous.

The rule ``/<action>/<item>`` matches as follows:

============ =========================================
Path         Result
============ =========================================
/save/123    ``{'action': 'save', 'item': '123'}``
/save/123/   `No Match`
/save/       `No Match`
//123        `No Match`
============ =========================================

You can change the exact behaviour in many ways using filters. This is described in the next section.

Wildcard Filters
--------------------------------------------------------------------------------

Filters are used to define more specific wildcards, and/or transform the matched part of the URL before it is passed to the callback. A filtered wildcard is declared as ``<name:filter>`` or ``<name:filter:config>``. The syntax for the optional config part depends on the filter used.

The following standard filters are implemented:

* **:int** matches (signed) digits and converts the value to integer.
* **:float** similar to :int but for decimal numbers.
* **:path** matches all characters including the slash character in a non-greedy way and may be used to match more than one path segment.
* **:re[:exp]** allows you to specify a custom regular expression in the config field. The matched value is not modified.

You can add your own filters to the router. All you need is derive a class from FilterMixin and reimplement parse method. This method must return twi elements: A regular expression string and callable to convert the URL fragment to a python value. The filter function is called with the configuration string as the only parameter and may parse it as needed::

    class ListFilter(btlroute.FilterMixin):

        delimiter = ','

        @classmethod
        def to_python(cls, match):
            return map(int, match.split(cls.delimiter))

        @classmethod
        def parse(cls, conf):
	    delimiter = config or cls.delimiter
	    return r'\d+(%s\d)*' % re.escape(delimiter), cls.to_python
    ...


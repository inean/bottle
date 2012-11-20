import unittest
import btlroute

class TestRouter(unittest.TestCase):
    def match(self, rule, url):
        return btlroute.Path(rule).match(url)

    def assertMatches(self, rule, url, **args):
        retval = self.match(rule, url)
        self.assertNotEqual(retval, None)
        self.assertEqual(args, retval)

    def testBasic(self):
        self.assertMatches('/static', '/static')
        self.assertMatches('/\\:its/:#.+#/:test/:name#[a-z]+#/',
                           '/:its/a/cruel/world/',
                           test='cruel', name='world')
        self.assertMatches('/:test', '/test', test='test') # No tail
        self.assertMatches(':test/', 'test/', test='test') # No head
        self.assertMatches('/:test/', '/test/', test='test') # Middle
        self.assertMatches(':test', 'test', test='test') # Full wildcard
        self.assertMatches('/:#anon#/match', '/anon/match') # Anon wildcards
        self.assertRaises(btlroute.RouteNotFoundError, self.match, '/:#anon#/match', '//no/m/at/ch/')

    def testNewSyntax(self):
        self.assertMatches('/static', '/static')
        self.assertMatches('/\\<its>/<:re:.+>/<test>/<name:re:[a-z]+>/',
                           '/<its>/a/cruel/world/',
                           test='cruel', name='world')
        self.assertMatches('/<test>', '/test', test='test') # No tail
        self.assertMatches('<test>/', 'test/', test='test') # No head
        self.assertMatches('/<test>/', '/test/', test='test') # Middle
        self.assertMatches('<test>', 'test', test='test') # Full wildcard
        self.assertMatches('/<:re:anon>/match', '/anon/match') # Anon wildcards
        self.assertRaises(btlroute.RouteNotFoundError, self.match, '/<:re:anon>/match', '//no/m/at/ch/')

    def testValueErrorInFilter(self):
        class TestFilter(btlroute.FilterMixin):
            @staticmethod
            def parse(conf): return r'-?\d+', int
        self.assertMatches('/int/<i:test>', '/int/5', i=5) # No tail
        self.assertRaises(btlroute.RouteNotFoundError, self.match, '/int/<i:test>', '//no/m/at/ch/')

    def testIntFilter(self):
        self.assertMatches('/object/<id:int>', '/object/567', id=567)
        self.assertRaises(btlroute.RouteNotFoundError, self.match, '/object/<id:int>', '/object/abc')

    def testFloatFilter(self):
        self.assertMatches('/object/<id:float>', '/object/1', id=1)
        self.assertMatches('/object/<id:float>', '/object/1.1', id=1.1)
        self.assertMatches('/object/<id:float>', '/object/.1', id=0.1)
        self.assertMatches('/object/<id:float>', '/object/1.', id=1)
        self.assertRaises(btlroute.RouteNotFoundError,  self.match, '/object/<id:float>', '/object/abc')
        self.assertRaises(btlroute.RouteNotFoundError,  self.match, '/object/<id:float>', '/object/')
        self.assertRaises(btlroute.RouteBadFilterError, self.match, '/object/<id:float>', '/object/.')

    def testPathFilter(self):
        self.assertMatches('/<id:path>/:f', '/a/b', id='a', f='b')
        self.assertMatches('/<id:path>', '/a', id='a')

    def testWildcardNames(self):
        self.assertMatches('/alpha/:abc', '/alpha/alpha', abc='alpha')
        self.assertMatches('/alnum/:md5', '/alnum/sha1', md5='sha1')

    def testParentheses(self):
        self.assertMatches('/func(:param)', '/func(foo)', param='foo')
        self.assertMatches('/func2(:param#(foo|bar)#)', '/func2(foo)', param='foo')
        self.assertMatches('/func2(:param#(foo|bar)#)', '/func2(bar)', param='bar')
        self.assertRaises(btlroute.RouteNotFoundError, self.match, '/func2(:param#(foo|bar)#)', '/func2(baz)')

    def testErrorInPattern(self):
        self.assertRaises(Exception, self.assertMatches, '/:bug#(#/', '/foo/')

if __name__ == '__main__': #pragma: no cover
    unittest.main()

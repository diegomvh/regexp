#!/usr/bin/env python

import unittest
from regexp.snippet import Snippet

class SnippetTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_parser(self):
        print(Snippet('''def ${1:fname}(${2:`if [ "$TM_CURRENT_LINE" != "" ]
				# poor man's way ... check if there is an indent or not
				# (cuz we would have lost the class scope by this point)
				then
					echo "self"
				fi`}):
	${3/.+/"""/}${3:docstring for $1}${3/.+/"""\n/}${3/.+/\t/}${0:pass}'''))
        
if __name__ == '__main__':
    unittest.main()
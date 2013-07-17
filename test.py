#!/usr/bin/env python

import re
import unittest

from regexp.snippet import Snippet, Visitor, SnippetHandler
from regexp.string import FormatString

class SnippetTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_parse_snippet(self):
        snippets = [
            '''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>''',
            '''class ${1:ClassName}(${2:object}):
	${3/.+/"""/}${3:docstring for $1}${3/.+/"""\n/}${3/.+/\t/}def __init__(self${4/([^,])?(.*)/(?1:, )/}${4:arg}):
		${5:super($1, self).__init__()}
${4/(\A\s*,\s*\Z)|,?\s*([A-Za-z_][a-zA-Z0-9_]*)\s*(=[^,]*)?(,\s*|$)/(?2:\t\tself.$2 = $2\n)/g}		$0'''
        ]
        for snippet in snippets:
            self.assertEqual(str(Snippet(snippet)), snippet)
    
    def test_parse_format_string(self):
        string = FormatString("storage.type.class.${1:/downcase}")
        print(string.replace({}))

    def test_snippet_holders(self):
        visitor = Visitor()
        snippet = SnippetHandler(Snippet('''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>'''))
        snippet.execute(visitor)
        print(visitor.output)
        snippet.insertText("hola mundo")
        snippet.render(visitor)
        print(visitor.output)
        print(snippet.next())
        
        #print(snippet.replace({"1": "hola mundo",
        #    "2": "id_cacho",
        #    "3": 2,
        #    "4": "my_name",
        #    "5": "hola value",
        #    "7": "id_input"}))
        
if __name__ == '__main__':
    unittest.main()
#! /usr/bin/env python

import markdown
import json
import sys
import datetime

# usage 
# prepend_to_changelog.py "Title string" path/to/description.md

if __name__ == '__main__':
    titlestr = sys.argv[1]
    descmdpath = sys.argv[2]

    with open('./changelog.json') as f:
        J = json.load(f)

    newitem = {}
    newitem['title'] = titlestr
    newitem['category'] = "Update"
    newitem['date'] = datetime.datetime.now().isoformat()
    with open(descmdpath) as f:
        deschtml = markdown.markdown(f.read())
    print "Adding new changelog item."
    print ""
    print "New item:"
    print ""
    print newitem
    print ""
    print "HTML Description:"
    print ""
    print deschtml
    print ""
    newitem['description'] = deschtml
    print "Any key to confirm:"
    raw_input()
    print ""

    J['items'].insert(0, newitem)
    with open('./changelog.json', 'w') as f:
        json.dump(J, f, indent=True)
    print "Done."
#!/bin/env python
"""
sitemap -- craw web site, record titles and links

see also: RDFIG chump entry
http://rdfig.xmlhack.com/2003/01/02/2003-01-02.html#1041485614.375205
and discussion
http://ilrt.org/discovery/chatlogs/rdfig/2003-01-02.html#T02-43-10

$Id$
see changelog at end.

Share and Enjoy.

design sketch:

1. content = urlopen.urlopen(startAddr)
2. xmlDoc = xmlparse(content)
3. neighbors = xpath.eval(xmlDoc, "//a/@href"); neighbors = map(lambda x: uripath.join(x, startAddr), neighbors)
4. title = xpath.eval(xmlDoc, "//title")
5. kb.addTriple(startAddr, dc.title, title)
6. for n in neighbors: kb.addTriple(startAddr, dc:relation, n)
7. queue unseen neighbors, recur

TODO:
  -- circles/arrows diagram of results
  -- handle img/@src
  -- handle area/@href
  -- handle form action?

LICENSE: Share and Enjoy.
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
Open Source license:
http://www.w3.org/Consortium/Legal/copyright-software-19980720

"""

import urllib2

# eliminate this dependency; use mnot's HtmlDom instead
# http://www.mnot.net/python/HtmlDom.py
# <AaronSw> it lets me do: d = fetch(url); print xml.xpath.Evaluate("//*[@class='rss:item']/text()", d)
import libxml2 # http://xmlsoft.org/python.html , DebianPackage:libxml2-python2.1 won't work because llyn.py uses 2.2isms

import llyn, uripath, toXML # http://www.w3.org/2000/10/swap/
from RDFSink import SYMBOL, LITERAL, FORMULA
import diag
diag.setVerbosity(0)

def DC(ln):
    return 'http://purl.org/dc/elements/1.1/' + ln

def RDFS(ln):
    return 'http://www.w3.org/2000/01/rdf-schema#' + ln


class Crawler:
    def __init__(self, kb, ctx, here):
        self._kb = kb
        self._ctx = ctx

    def crawlFrom(self, addr, prefix, max):
        kb = self._kb
        ctx = self._ctx

        iter = 1
        queue = [addr]
        seen = []
        while queue:
            head = queue.pop()

            progress("crawling at: ", head, " iter ", iter, " of ", max)
            iter = iter + 1
            if iter > max:
                progress ("max limit reached.")
                break

            seen.append(head)

            try:
                rep = urllib2.urlopen(head)
                content = rep.read()
            except IOError:
                progress("can't GET", head)
                continue
                #@@ makeStatement(head type NoGood)

            # try to find a short label for
            # a diagram or some such.
            # try the last path segment,
            # or the 2nd last in case of an empty last segment...
            slash = head[:-1].rfind('/')
            label = head[slash+1:]
            
            ct = rep.info().getheader('content-type')
            progress("... got content of type ", ct)
            isHTML = ct.find('text/html') == 0

            kb.makeStatement((ctx,
                              kb.newSymbol(DC('type')),
                              kb.newSymbol(head),
                              kb.newLiteral(ct)))

            # note that we're not peeking into the URI
            # to find out if it's HTML; we're just
            # eliding the extension in the case we
            # know (from the HTTP headers) that it's HTML.
            if isHTML and label[-5:] == '.html':
                label = label[:-5]

            kb.makeStatement((ctx,
                              kb.newSymbol(RDFS('label')),
                              kb.newSymbol(head),
                              kb.newLiteral(label)))

            if not isHTML: continue
            
            progress("... parsing text/html content")
            doc = libxml2.htmlParseDoc(content, 'us-ascii')
            try:
                titles = doc.xpathNewContext().xpathEval('//title')
                title = titles[0].getContent()
            except: #@@figure out the right exceptions
                pass
            else:
                progress("... found title:", title)
                #self._fmla.add(DC('title'), head, str(title))
                kb.makeStatement((ctx,
                                  kb.newSymbol(DC('title')),
                                  kb.newSymbol(head),
                                  kb.newLiteral(str(title))))
            
            hrefs = doc.xpathNewContext().xpathEval('//a/@href')
            progress("... found ", len(hrefs), " links")
                     
            for h in hrefs:
                h = h.getContent()
                progress("... found href", h)
                i = uripath.join(head, h)
                progress("... found link", head, ' -> ', i)
                kb.makeStatement((ctx,
                                  kb.newSymbol(DC('relation')),
                                  kb.newSymbol(head),
                                  kb.newSymbol(i)))
                if i[:len(prefix)] == prefix and i not in seen:
                    queue.append(i)


def progress(*args):
    import sys
    for a in args:
        sys.stderr.write('%s ' % a)
    sys.stderr.write("\n")


def main(argv):
    import sys

    site, max = argv[1:3]
    max = int(max)
    kb = llyn.RDFStore()
    here = uripath.base()
    f = kb.intern((FORMULA, here + "#_formula")) #@@ ugly!
    progress("f = ", f)
    c = Crawler(kb, f, here)
    c.crawlFrom(site, site, max)
    sink = toXML.ToRDF(sys.stdout, here)
    sink.bind('dc', DC(''))
    sink.bind('s', RDFS(''))
    kb.dumpNested(f, sink)
    
if __name__ == '__main__':
    import sys
    main(sys.argv)

# $Log$
# Revision 1.3  2003-01-03 04:18:32  connolly
# added rdfs:label for use with circles and arrows tools; added dc:type while I was at it
#
# Revision 1.2  2003/01/02 05:32:46  connolly
# some comments about dependencies
#
# Revision 1.1  2003/01/02 05:29:59  connolly
# works on one web site
#

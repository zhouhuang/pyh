# @file: pyh.py
# @purpose: a HTML tag generator
# @author: Emmanuel Turlay <turlay@cern.ch>

__doc__ = """The pyh.py module is the core of the PyH package. PyH lets you
generate HTML tags from within your python code.
See http://code.google.com/p/pyh/ for documentation.
"""
__author__ = "Emmanuel Turlay <turlay@cern.ch>"
__version__ = '$Revision: 19 $'
__date__ = '$Date$'

from sys import _getframe, stdout, modules, version
nOpen={}

nl = '\n'
br = '<br />'+nl
doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
charset = '<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'

tags = ['html', 'body', 'head', 'link', 'meta', 'div', 'p', 'form', 'legend', 
        'input', 'select', 'span', 'b', 'i', 'option', 'img', 'script',
        'table', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'fieldset', 'a', 'title']

selfClose = ['input', 'img', 'link']

class Tag(list):
    tagname = ''

    def __init__(self, *arg, **kw):
        self.attributes = kw
        if self.tagname : 
            name = self.tagname
            self.isSeq = False
        else: 
            name = 'sequence'
            self.isSeq = True
        self.id = kw.get('id', name)
        self.extend(arg)
        for a in arg: self.addObj(a)

    def __iadd__(self, obj):
        if isinstance(obj, Tag):
            if obj.isSeq: 
                for o in obj: self.addObj(o)
            else: 
                self.addObj(obj)
        else: self.addObj(obj, 'content')
        return self
    
    def addObj(self, obj, id=''):
        if isinstance(obj, Tag): id = obj.id
        self.append(obj)
        setattr(self, obj, id)

    def __add__(self, obj):
        if self.tagname: return Tag(self, obj)
        self.addObj(obj)
        return self

    def render(self):
        result = ''
        if self.tagname:
            result = '<%s%s%s>' % (self.tagname, self.renderAtt(), self.selfClose()*' /')
        if not self.selfClose():
            for c in self:
                if isinstance(c, Tag):
                    result += c.render()
                else: result += c
        if len(self) and self.tagname: 
            result += '</%s>' % self.tagname
        return result

    def renderAtt(self):
        result = ''
        for n, v in self.attributes:
            if n != 'txt' and n != 'open':
                if n == 'cl': n = 'class'
                result += ' %s="%s"' % (n, v)
        return result

    def selfClose(self):
        return self.tagname in selfClose
    
def TagFactory(name):
    class f(Tag):
        tagname = name
    return f

thisModule = modules[__name__]

for t in tags: setattr(thisModule, t, TagFactory(t)) 

def ValidW3C():
    out = a(href='http://validator.w3.org/check?uri=referer',
                    txt=img(src='http://www.w3.org/Icons/valid-xhtml10', alt='Valid XHTML 1.0 Strict'))
    return out

class PyH (Tag):
    header, footer = '', ''
    tagname = 'body'
    javascripts, stylesheets, _meta = [], [], []
    lang = 'en'
    def __init__(self, title='MyPyHPage'):
        self.title = title
        self.counter = TagCounter(title)
    
    def addMeta(self, name='', content='', http_equiv=''):
        if content:
            meta = {'content':content, 'name':name, 'http-equiv':http_equiv}

    def tag(self, **kw):
        "Core function to generate tags"
        noNewLine = ['td', 'th', 'input']
        selfClose = ['input', 'img', 'link']
        _name = kw.get('tagname', None)
        if not isLegal(_name): return ''
        open = kw.get('open', 'cl' in kw or 'id' in kw or c.isClosed(_name))
        c = self._counter
        if not c.isAllowed(_name, open) : return ''
        out = '<%s%s' % ((not open) * '/', _name)
        if open:
            c.open(_name)
            for i,v in kw.iteritems():
                if i != 'txt' and i != 'open':
                    if i == 'cl': i = 'class'
                    out += ' %s="%s"' % (i, v)
        else: c.close(_name)
        if _name in selfClose:
            out += ' /'
            c.close(_name)
        out += '>'
        if 'txt' in kw.keys() or ('src' in kw.keys() and _name != 'img'):
            out += '%s%s' % (kw.get('txt', ''), '</%s>' % _name)
            c.close(_name)
        if not open and _name not in noNewLine: out += nl
        return out
    
    def printOut(self,file=''):
        if file: f = open(file, 'w')
        else: f = stdout
        self += doctype
        html = self.renderHeader()
        html += self
        f.write(html.render())
        f.flush()
        f.close()

    def renderHeader(self):
        h = html(xmlns='http://www.w3.org/1999/xhtml', lang=self._lang)
        he = head()
        he += charset
        he += title(txt=self._title)
        for s in self._stylesheets:
            he += link(rel='stylesheet',type='text/css',href=s)
        for j in self._javascripts:
            he += script(type='text/javascript',src=j)
        h += he
        return h

    def renderFooter(self):
        f = self._footer
        f += body()
        f += html()
        return f
    
class TagCounter:
    _count = {}
    _lastOpen = []
    for t in tags: _count[t] = 0
    def __init__(self, name):
        self._name = name
    def open(self, tag):
        if isLegal(tag): 
            self._count[tag] += 1
            self._lastOpen += [tag]
    def close(self, tag):
        if isLegal(tag) and self._lastOpen[-1] == tag: 
            self._count[tag] -= 1
            self._lastOpen.pop()
        else:
            print 'Cross tagging is wrong'
    def isAllowed(self, tag, open):
        if not open and self.isClosed(tag):
            print 'TRYING TO CLOSE NON-OPEN TAG: %s' % tag
            return False
        return True
    def isOpen(self, tag):
        if isLegal(tag): return self._count[tag]
    def isClosed(self, tag):
        if isLegal(tag): return not self._count[tag]

    
def isLegal(tag):
    if tag in tags: return True
    else:
        print 'ILLEGAL TAG: %s' % tag
        return False

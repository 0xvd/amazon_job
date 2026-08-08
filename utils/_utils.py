import collections
import itertools
import re
import html.parser
import contextlib
import re
import json

class NO_DEFAULT:...

def IDENTITY(x):
    return x

class compat_HTMLParseError(ValueError):
    pass

class Parser(html.parser.HTMLParser):
    attrs = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is None:
            self.attrs = dict(attrs)

def hidden_inputs(html):
    hidden_inputs = {}
    for input_el in re.findall(r'(?i)(<input[^>]+>)', html):
        attrs = extract_attributes(input_el)
        if not input_el:
            continue
        if attrs.get('type') not in ('hidden', 'submit'):
            continue
        name = attrs.get('name') or attrs.get('id')
        value = attrs.get('value')
        if name and value is not None:
            hidden_inputs[name] = value
    return hidden_inputs

def extract_attributes(html):
    parser = Parser()
    parser.feed(html)
    return parser.attrs or {}

def search_regex(pattern, string, default=None, flags=0, group=None):
    if string is None:
        mobj = None
    elif isinstance(pattern, (str, re.Pattern)):
        mobj = re.search(pattern, string, flags)
    else:
        for p in pattern:
            mobj = re.search(p, string, flags)
            if mobj:
                break

    if mobj:
        if group is None:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif isinstance(group, (list, tuple)):
            return tuple(mobj.group(g) for g in group)
        else:
            return mobj.group(group)
    return default

def search_json(start_pattern, string, name, end_pattern='',
                 contains_pattern=r'{(?s:.+)}', default=None):
 
    json_string = search_regex(rf'(?:{start_pattern})\s*(?P<json>{contains_pattern})\s*(?:{end_pattern})', string, name, group='json', default=default)
    if not json_string:
        return default

    try:
        return json.loads(json_string)
    except Exception:
        return default
    except json.JSONDecodeError:
        return default

def url_or_none(url):
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    return url if re.match(r'(?:(?:https?|rtm(?:pt?[es]?|fp)|ftps?|wss?):)?//', url) else None

def is_iterable_like(x, allowed_types=collections.abc.Iterable, blocked_types=NO_DEFAULT):
    if blocked_types is NO_DEFAULT:
        blocked_types = (str, bytes, collections.abc.Mapping)
    return isinstance(x, allowed_types) and not isinstance(x, blocked_types)


def variadic(x, allowed_types=NO_DEFAULT):
    if not isinstance(allowed_types, (tuple, type)):
        allowed_types = tuple(allowed_types)
    return x if is_iterable_like(x, blocked_types=allowed_types) else (x, )

def try_call(*funcs, expected_type=None, args=[], kwargs={}):
    for f in funcs:
        try:
            val = f(*args, **kwargs)
        except (AttributeError, KeyError, TypeError, IndexError, ValueError, ZeroDivisionError):
            pass
        else:
            if expected_type is None or isinstance(val, expected_type):
                return val

def unescapeHTML(s):
    if s is None:
        return None
    assert isinstance(s, str)

    return re.sub(
        r'&([^&;]+;)', lambda m: _htmlentity_transform(m.group(1)), s)

def _htmlentity_transform(entity_with_semicolon):
    """Transforms an HTML entity to a character."""
    entity = entity_with_semicolon[:-1]

    # Known non-numeric HTML entity
    if entity in html.entities.name2codepoint:
        return chr(html.entities.name2codepoint[entity])

    # TODO: HTML5 allows entities without a semicolon.
    # E.g. '&Eacuteric' should be decoded as 'Éric'.
    if entity_with_semicolon in html.entities.html5:
        return html.entities.html5[entity_with_semicolon]

    mobj = re.match(r'#(x[0-9a-fA-F]+|[0-9]+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith('x'):
            base = 16
            numstr = f'0{numstr}'
        else:
            base = 10
        # See https://github.com/ytdl-org/youtube-dl/issues/7518
        with contextlib.suppress(ValueError):
            return chr(int(numstr, base))

    # Unknown entity in name, return its literal representation
    return f'&{entity};'

def get_element_by_id(id, html, **kwargs):
    """Return the content of the tag with the specified ID in the passed HTML document"""
    return get_element_by_attribute('id', id, html, **kwargs)


def get_element_html_by_id(id, html, **kwargs):
    """Return the html of the tag with the specified ID in the passed HTML document"""
    return get_element_html_by_attribute('id', id, html, **kwargs)


def get_element_by_class(class_name, html):
    """Return the content of the first tag with the specified class in the passed HTML document"""
    retval = get_elements_by_class(class_name, html)
    return retval[0] if retval else None


def get_element_html_by_class(class_name, html):
    """Return the html of the first tag with the specified class in the passed HTML document"""
    retval = get_elements_html_by_class(class_name, html)
    return retval[0] if retval else None


def get_element_by_attribute(attribute, value, html, **kwargs):
    retval = get_elements_by_attribute(attribute, value, html, **kwargs)
    return retval[0] if retval else None


def get_element_html_by_attribute(attribute, value, html, **kargs):
    retval = get_elements_html_by_attribute(attribute, value, html, **kargs)
    return retval[0] if retval else None


def get_elements_by_class(class_name, html, **kargs):
    """Return the content of all tags with the specified class in the passed HTML document as a list"""
    return get_elements_by_attribute(
        'class', rf'[^\'"]*(?<=[\'"\s]){re.escape(class_name)}(?=[\'"\s])[^\'"]*',
        html, escape_value=False)


def get_elements_html_by_class(class_name, html):
    """Return the html of all tags with the specified class in the passed HTML document as a list"""
    return get_elements_html_by_attribute(
        'class', rf'[^\'"]*(?<=[\'"\s]){re.escape(class_name)}(?=[\'"\s])[^\'"]*',
        html, escape_value=False)


def get_elements_by_attribute(*args, **kwargs):
    """Return the content of the tag with the specified attribute in the passed HTML document"""
    return [content for content, _ in get_elements_text_and_html_by_attribute(*args, **kwargs)]


def get_elements_html_by_attribute(*args, **kwargs):
    """Return the html of the tag with the specified attribute in the passed HTML document"""
    return [whole for _, whole in get_elements_text_and_html_by_attribute(*args, **kwargs)]


def get_elements_text_and_html_by_attribute(attribute, value, html, *, tag=r'[\w:.-]+', escape_value=True):
    """
    Return the text (content) and the html (whole) of the tag with the specified
    attribute in the passed HTML document
    """
    if not value:
        return

    quote = '' if re.match(r'''[\s"'`=<>]''', value) else '?'

    value = re.escape(value) if escape_value else value

    partial_element_re = rf'''(?x)
        <(?P<tag>{tag})
         (?:\s(?:[^>"']|"[^"]*"|'[^']*')*)?
         \s{re.escape(attribute)}\s*=\s*(?P<_q>['"]{quote})(?-x:{value})(?P=_q)
        '''

    for m in re.finditer(partial_element_re, html):
        content, whole = get_element_text_and_html_by_tag(m.group('tag'), html[m.start():])

        yield (
            unescapeHTML(re.sub(r'^(?P<q>["\'])(?P<content>.*)(?P=q)$', r'\g<content>', content, flags=re.DOTALL)),
            whole,
        )


class HTMLBreakOnClosingTagParser(html.parser.HTMLParser):
    """
    HTML parser which raises HTMLBreakOnClosingTagException upon reaching the
    closing tag for the first opening tag it has encountered, and can be used
    as a context manager
    """

    class HTMLBreakOnClosingTagException(Exception):
        pass

    def __init__(self):
        self.tagstack = collections.deque()
        html.parser.HTMLParser.__init__(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        # handle_endtag does not return upon raising HTMLBreakOnClosingTagException,
        # so data remains buffered; we no longer have any interest in it, thus
        # override this method to discard it
        pass

    def handle_starttag(self, tag, _):
        self.tagstack.append(tag)

    def handle_endtag(self, tag):
        if not self.tagstack:
            raise compat_HTMLParseError('no tags in the stack')
        while self.tagstack:
            inner_tag = self.tagstack.pop()
            if inner_tag == tag:
                break
        else:
            raise compat_HTMLParseError(f'matching opening tag for closing {tag} tag not found')
        if not self.tagstack:
            raise self.HTMLBreakOnClosingTagException


# XXX: This should be far less strict
def get_element_text_and_html_by_tag(tag, html):
    """
    For the first element with the specified tag in the passed HTML document
    return its' content (text) and the whole element (html)
    """
    def find_or_raise(haystack, needle, exc):
        try:
            return haystack.index(needle)
        except ValueError:
            raise exc
    closing_tag = f'</{tag}>'
    whole_start = find_or_raise(
        html, f'<{tag}', compat_HTMLParseError(f'opening {tag} tag not found'))
    content_start = find_or_raise(
        html[whole_start:], '>', compat_HTMLParseError(f'malformed opening {tag} tag'))
    content_start += whole_start + 1
    with HTMLBreakOnClosingTagParser() as parser:
        parser.feed(html[whole_start:content_start])
        if not parser.tagstack or parser.tagstack[0] != tag:
            raise compat_HTMLParseError(f'parser did not match opening {tag} tag')
        offset = content_start
        while offset < len(html):
            next_closing_tag_start = find_or_raise(
                html[offset:], closing_tag,
                compat_HTMLParseError(f'closing {tag} tag not found'))
            next_closing_tag_end = next_closing_tag_start + len(closing_tag)
            try:
                parser.feed(html[offset:offset + next_closing_tag_end])
                offset += next_closing_tag_end
            except HTMLBreakOnClosingTagParser.HTMLBreakOnClosingTagException:
                return html[content_start:offset + next_closing_tag_start], \
                    html[whole_start:offset + next_closing_tag_end]
        raise compat_HTMLParseError('unexpected end of html')


class HTMLAttributeParser(html.parser.HTMLParser):
    """Trivial HTML parser to gather the attributes for a single element"""

    def __init__(self):
        self.attrs = {}
        html.parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        self.attrs = dict(attrs)
        raise compat_HTMLParseError('done')


class HTMLListAttrsParser(html.parser.HTMLParser):
    """HTML parser to gather the attributes for the elements of a list"""

    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.items = []
        self._level = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'li' and self._level == 0:
            self.items.append(dict(attrs))
        self._level += 1

    def handle_endtag(self, tag):
        self._level -= 1


def extract_attributes(html_element):
    """Given a string for an HTML element such as
    <el
         a="foo" B="bar" c="&98;az" d=boz
         empty= noval entity="&amp;"
         sq='"' dq="'"
    >
    Decode and return a dictionary of attributes.
    {
        'a': 'foo', 'b': 'bar', c: 'baz', d: 'boz',
        'empty': '', 'noval': None, 'entity': '&',
        'sq': '"', 'dq': '\''
    }.
    """
    parser = HTMLAttributeParser()
    with contextlib.suppress(compat_HTMLParseError):
        parser.feed(html_element)
        parser.close()
    return parser.attrs

class LazyList(collections.abc.Sequence):
    """Lazy immutable list from an iterable
    Note that slices of a LazyList are lists and not LazyList"""

    class IndexError(IndexError):  # noqa: A001
        pass

    def __init__(self, iterable, *, reverse=False, _cache=None):
        self._iterable = iter(iterable)
        self._cache = [] if _cache is None else _cache
        self._reversed = reverse

    def __iter__(self):
        if self._reversed:
            # We need to consume the entire iterable to iterate in reverse
            yield from self.exhaust()
            return
        yield from self._cache
        for item in self._iterable:
            self._cache.append(item)
            yield item

    def _exhaust(self):
        self._cache.extend(self._iterable)
        self._iterable = []  # Discard the emptied iterable to make it pickle-able
        return self._cache

    def exhaust(self):
        """Evaluate the entire iterable"""
        return self._exhaust()[::-1 if self._reversed else 1]

    @staticmethod
    def _reverse_index(x):
        return None if x is None else ~x

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if self._reversed:
                idx = slice(self._reverse_index(idx.start), self._reverse_index(idx.stop), -(idx.step or 1))
            start, stop, step = idx.start, idx.stop, idx.step or 1
        elif isinstance(idx, int):
            if self._reversed:
                idx = self._reverse_index(idx)
            start, stop, step = idx, idx, 0
        else:
            raise TypeError('indices must be integers or slices')
        if ((start or 0) < 0 or (stop or 0) < 0
                or (start is None and step < 0)
                or (stop is None and step > 0)):
            # We need to consume the entire iterable to be able to slice from the end
            # Obviously, never use this with infinite iterables
            self._exhaust()
            try:
                return self._cache[idx]
            except IndexError as e:
                raise self.IndexError(e) from e
        n = max(start or 0, stop or 0) - len(self._cache) + 1
        if n > 0:
            self._cache.extend(itertools.islice(self._iterable, n))
        try:
            return self._cache[idx]
        except IndexError as e:
            raise self.IndexError(e) from e

    def __bool__(self):
        try:
            self[-1] if self._reversed else self[0]
        except self.IndexError:
            return False
        return True

    def __len__(self):
        self._exhaust()
        return len(self._cache)

    def __reversed__(self):
        return type(self)(self._iterable, reverse=not self._reversed, _cache=self._cache)

    def __copy__(self):
        return type(self)(self._iterable, reverse=self._reversed, _cache=self._cache)

    def __repr__(self):
        # repr and str should mimic a list. So we exhaust the iterable
        return repr(self.exhaust())

    def __str__(self):
        return repr(self.exhaust())


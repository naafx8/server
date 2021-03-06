__pragma__('alias', 'S', '$')  # JQuery

from client import (client, thumbclient, Base, Command, ItemType)


class Widget(Base):

    def __init__(self, source_el):
        super().__init__()
        self._source_el = source_el
        self.node = None
        self._events = {}

    def register(self, event_name):
        "register event, best used in __init__"
        self._events[event_name] = []

    def on(self, event_name, callback):
        "much like jquery events"
        assert callable(callback)
        if event_name in self._events:
            self._events[event_name].append(callback)

    __pragma__('kwargs')
    def call(self, event_name, *args, **kwargs):
        "call event with args and kwargs"
        if event_name in self._events:
            for c in self._events[event_name]:
                c(*args, **kwargs)
        else:
            self.log("No such event '{}' by {}".format(event_name, self))
    __pragma__('nokwargs')

    def data(self):
        raise NotImplementedError

    __pragma__('kwargs')

    def compile(
            self,
            target_el,
            after=None,
            before=None,
            append=None,
            prepend=None):
        """
        Compile widget into target element
        Set after, before, append or prepend to True to specify where to insert html.
        """
        self.node = super().compile(self._source_el, target_el,
                               after=after, before=before,
                               append=append, prepend=prepend,
                               **self.data())
        return self.node

    __pragma__('nokwargs')

    def get_node(self):

        if not self.node:
            self.node = S(self._source_el)

        return self.node


class Thumbnail(Widget):

    def __init__(self, source_el, size_type, item_type, id):
        super().__init__(source_el)
        self.thumbclient = thumbclient
        self.item_type = item_type
        self.size_type = size_type
        self.id = id
        self._thumbs = {
            'Big': None,
            'Medium': None,
            'Small': None
        }
        self._thumbsize = None
        self._fetched_event = 'fetched'
        self.register(self._fetched_event)
        self._fetched = False

    __pragma__('tconv')
    __pragma__('kwargs')

    def _fetch_thumb(self, data=None, error=None, size='Big'):
        if data is not None and not error:
            cmd_id = data[str(self.id)]
            if cmd_id:
                cmd = Command(cmd_id)
                self._thumbs[self._thumbsize] = cmd
                cmd.set_callback(self._set_thumb_cmd)
                cmd.poll_until_complete(500)
        elif error:
            pass
        else:
            if self.id is not None:
                self._thumbsize = size
                self.thumbclient.call_func("get_image", self._fetch_thumb, item_ids=[self.id],
                                 size=size, url=True, uri=True, item_type=self.item_type)
    __pragma__('notconv')
    __pragma__('nokwargs')

    __pragma__('tconv')

    def _set_thumb_cmd(self, cmd):
        val = cmd.get_value()
        im = None
        if val:
            im = val['data']

        self._thumbs[self._thumbsize] = val

        if not im:
            im = "/static/img/no-image.png"

        self._set_thumb(im)
    __pragma__('notconv')

    def _set_thumb(self, im):
        if self.get_node() and im:
            self._fetched = True
            self.node.find('img').attr('src', im)
            self.node.find('.load').fadeOut(300)
            self.call(self._fetched_event)

    __pragma__('tconv')

    def fetch_thumb(self):
        if not self.size_type or self._fetched:
            return

        s = {
            'big': 'Big',
            'medium': 'Medium',
            'small': 'Small'
        }

        size = s[self.size_type]
        if self._thumbs[size]:
            self._set_thumb(self._thumbs[size])
        else:
            self._fetch_thumb(size=size)
    __pragma__('notconv')

    __pragma__('kwargs')

    def compile(
            self,
            target_el,
            after=None,
            before=None,
            append=None,
            prepend=None):
        """
        Compile widget into target element
        Set after, before, append or prepend to True to specify where to insert html.
        """
        self.node = super().compile(target_el,
                               after=after, before=before,
                               append=append, prepend=prepend,
                               **self.data())
        S(self.node).one('inview', self.fetch_thumb)
        return self.node

    __pragma__('nokwargs')

class MassThumbnail:

    def __init__(self, thumbs, item_type):
        self.thumbs = thumbs
        self.item_type = item_type
        self._cmd_map = {}
        self._thumb_map = {}
        self._thumbsize = None
        self._callback = None
        self.cmd = None

    __pragma__('kwargs')
    def mass_fetch(self, size_type, callback=None):
        ""
        self._callback = callback
        self._thumb_map.clear()
        ids = []
        for t in self.thumbs:
            assert isinstance(t, Thumbnail)
            ids.append(t.id)
            self._thumb_map[t.id] = t

        s = {
            'big': 'Big',
            'medium': 'Medium',
            'small': 'Small'
        }

        size = s[size_type]

        self._mass_get(ids=ids, size=size)
    __pragma__('nokwargs')

    __pragma__('tconv')
    __pragma__ ('jsiter')
    __pragma__('kwargs')
    def _mass_get(self, data=None, error=None, ids=[], size='Big'):
        if data is not None and not error:
            self._cmd_map.clear()
            cmd_ids = []
            for i in data:
                cmd_id = data[i]
                cmd_ids.append(cmd_id)
                self._cmd_map[cmd_id] = int(i)

            if cmd_ids:
                self.cmd = Command(cmd_ids)
                self.cmd.set_callback(self._mass_set, True)
                self.cmd.poll_until_complete(500)
        elif error:
            pass
        else:
            if ids:
                self._thumbsize = size
                thumbclient.call_func("get_image", self._mass_get, item_ids=ids,
                                 size=size, url=True, uri=True, item_type=self.item_type)
    __pragma__('nokwargs')
    __pragma__ ('nojsiter')
    __pragma__('notconv')

    def _mass_set(self, cmd, value):
        im = None
        if value:
            im = value['data']

        tid = self._cmd_map[cmd]
        thumb = self._thumb_map[tid]
        thumb._thumbs[self._thumbsize] = im
        if not im:
            im = "/static/img/no-image.png"
        thumb._set_thumb(im)

        if self.cmd and self._callback and self.cmd.done():
            self._callback()

class Gallery(Thumbnail):

    __pragma__('kwargs')

    def __init__(self, gtype='medium', gallery_obj={}):
        self.obj = gallery_obj
        self.id = 0
        if 'id' in self.obj:
            self.id = self.obj['id']
        super().__init__("#gallery-" + gtype + "-t", gtype, ItemType.get('gallery'), self.id)
        self._gtype = gtype
        self.artists = []
    __pragma__('nokwargs')

    __pragma__('tconv')

    def title(self):
        "Returns title in preffered language"
        t = ""

        if self.obj:
            if self.obj['titles']:
                t = self.obj['titles'][0]['name']

        return t
    __pragma__('notconv')

    def titles(self):
        "Returns all titles"
        pass

        return a

    __pragma__('tconv')
    def _fetch_artists(self, data=None, error=None):
        if data is not None and not error:
            self.artists = data

            if self.node and self.artists:
                anames = data[0]['names']
                if anames:
                    anode = self.node.find('.gartist')
                    anode.text(anames[0]['name'])

        elif error:
            pass
        else:
            client.call_func("get_related_items", self._fetch_artists, item_id=self.id,
                                  item_type=self.item_type, related_type=ItemType.get('artist'))
    __pragma__('notconv')


    __pragma__('tconv')

    def data(self):
        g = {}
        g['id'] = self.obj['id']

        if self._gtype == 'medium':
            g['title'] = self.title()
            g['thumb'] = "/static/img/default.png"

        if not self.artists:
            self._fetch_artists()

        return g

    __pragma__('notconv')


class Page(Thumbnail):

    __pragma__('kwargs')

    def __init__(self, stype='medium', obj={}):
        self.obj = obj
        self.id = 0
        if 'id' in self.obj:
            self.id = self.obj['id']
        super().__init__("#page-" + stype + "-t", stype, ItemType.get('page'), self.id)
        self._stype = stype
    __pragma__('nokwargs')

    __pragma__('tconv')
    def number(self):
        n = 0
        if self.obj:
            n = self.obj['number']
        return n
    __pragma__('notconv')

    __pragma__('tconv')
    def name(self):
        n = ""
        if self.obj:
            n = self.obj['name']
        return n
    __pragma__('notconv')

    __pragma__('tconv')

    def data(self):
        o = {}
        o['id'] = self.id

        if self._stype == 'medium':
            o['name'] = self.name()
            o['number'] = str(self.number())
            o['thumb'] = "/static/img/default.png"

        return o

    __pragma__('notconv')

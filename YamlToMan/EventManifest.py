import simple_xml as xml
import collections, re

def make_symbol(*args):
    return re.sub('[^0-9A-Z]+', '_', '_'.join(args).upper())

class ManifestBase:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

class Provider(ManifestBase):
    def __init__(self, name):
        super().__init__(name)
        self.contents = collections.defaultdict(lambda: [])

    def add(self, obj):
        container = self.contents[obj.__class__.__name__.lower()]
        container.append(obj)

    def container(self, name):
        if (name in self.contents):
            return self.contents[name]

        return []

    @property
    def guid(self):
        return "guid."

    @property
    def binary_filename(self):
        return "%temp%/pork.dll"

class ItemBase(ManifestBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self._message = kwargs.get("message", None)

    @property
    def value(self):
        return 0

    @property
    def message(self):
        return self._message

class Event(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

        self._channel = kwargs.get("channel", None)
        self._task = kwargs.get("task", None)
        self._opcode = kwargs.get("opcode", None)
        self._keywords = kwargs.get("keywords", None)
        self._level = kwargs.get("level", None)
        self._template = kwargs.get("template", None)

    @property
    def channel(self):
        return self._channel

    @property
    def task(self):
        return self._task

    @property
    def opcode(self):
        return self._opcode

    @property
    def keywords(self):
        return self._keywords

    @property
    def level(self):
        return self._level

    @property
    def template(self):
        return self._template


class Task(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

class Opcode(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

class Keyword(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    @property
    def mask(self):
        return "0x1"

class Filter(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    @property
    def template(self):
        return None

class Level(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    @property
    def level(self):
        return 16 # 16-255

class Template(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self._data = []

    def add_data(self, name, type):
        self._data.append((name, type))

    @property
    def data(self):
        return self._data

class Channel(ItemBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    @property
    def enabled(self):
        return True

    @property
    def type(self):
        return "Admin"

def to_manifest_xml(providers):
    root = xml.Node(
        'instrumentationManifest',
        xmlns = "http://schemas.microsoft.com/win/2004/08/events"
        )

    instrumentation = root.add('instrumentation')
    instrumentation.attrs({
        'xmlns:win': "http://manifests.microsoft.com/win/2004/08/windows/events",
        'xmlns:xs': "http://www.w3.org/2001/XMLSchema",
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"
    })

    container_root = instrumentation.add('events')
    container_root.attrs(xmlns = "http://schemas.microsoft.com/win/2004/08/events")

    for p in providers:
        provider = container_root.add('provider',
            name = p.name,
            symbol = make_symbol(p.name),
            guid = p.guid,
            messageFileName = p.binary_filename,
            resourceFileName = p.binary_filename
        )

        def build_container(provider, xml, name, build):
            cnt = p.container(name)
            xml_cnt = provider.add(name + 's')
            for o in cnt:
                xml = xml_cnt.add(name)

                build(xml, o)

        def build_event(xml, evt):
            xml.attrs(
                symbol = make_symbol(p.name, "event", evt.name),
                template = evt.template.name if evt.template else None,
                value = evt.value,
                level = evt.level.name if evt.level else None,
                channel = evt.channel.name if evt.channel else None,
                task = evt.task.name if evt.task else None,
                opcode = evt.opcode.name if evt.opcode else None,
                keywords = evt.keywords.name if evt.keywords else None,
                message = evt.message
            )
        build_container(provider, p, 'event', build_event)

        def build_task(xml, task):
            xml.attrs(
                name = task.name,
                symbol = make_symbol(p.name, "task", task.name),
                value = task.value,
                message = task.message
            )
        build_container(provider, p, 'task', build_task)


        def build_opcode(xml, opcode):
            xml.attrs(
                name = opcode.name,
                symbol = make_symbol(p.name, "opcode", opcode.name),
                value = opcode.value,
                message = opcode.message
            )
        build_container(provider, p, 'opcode', build_opcode)

        def build_keyword(xml, keyword):
            xml.attrs(
                name = keyword.name,
                mask = keyword.mask
            )
        build_container(provider, p, 'keyword', build_keyword)

        def build_filter(xml, filter):
            xml.attrs(
                name = filter.name,
                value = filter.value,
                tid = filter.template.name if filter.template else None,
                symbol = make_symbol(p.name, "filter", filter.name),
            )
        build_container(provider, p, 'filter', build_filter)

        def build_level(xml, level):
            xml.attrs(
                name = level.name,
                value = level.value,
                symbol = make_symbol(p.name, "level", level.name),
                message = level.message
            )
        build_container(provider, p, 'level', build_level)

        def build_channel(xml, channel):
            xml.attrs(
                chid = channel.name,
                name = "{}/{}".format(channel.name, channel.type),
                type = channel.type,
                enabled = channel.enabled
            )
        build_container(provider, p, 'channel', build_channel)

        def build_template(xml, template):
            xml.attrs(
                tid = template.name
            )

            for d in template.data:
                data_xml = xml.add(
                    'data',
                    name = d[0],
                    inType = d[1]
                )

        build_container(provider, p, 'template', build_template)

    return root.to_xml_document()


p = Provider("Multi-Main")

task = Task("task1")
p.add(task)

op = Opcode("opcode")
p.add(op)

kw = Keyword("kw")
p.add(kw)

filter = Filter("fil")
p.add(filter)

lev = Level("lev")
p.add(lev)

templ = Template("cha")
templ.add_data("Description", "win:AnsiString")
p.add(templ)

channel = Channel("kchaw")
p.add(channel)

ev = Event("pork",
    channel = channel,
    task = task,
    opcode = op,
    keywords = kw,
    level = lev,
    template = templ
    )
p.add(ev)


print(to_manifest_xml([p]))

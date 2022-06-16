# Utility functions
import os
import datetime as dt
import nextcord
import collections.abc

SPACE = '\u200B'
EMPTY = nextcord.Embed.Empty

def full_path(*args):
    return os.path.join(*args)

def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

# handy function to split list l into chunks of length n
def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n] 

class Ames_logger():
    def __init__(self, cog_name, log):
        self.logc   = None
        self.logf   = log
        self.name   = cog_name
        #self.client = None

    def init_client(self, client):
        #self.client = client
        logc_config = client.config['ames_logger']
        self.logc = client.get_guild(logc_config['guild_id']).get_channel(logc_config['channel_id'])
    
    def _clean_msg(self, msg):
        msg = [str(w) for w in msg]
        return ' '.join([self.name, *msg])

    async def send(self, *msg):
        await self.logc.send(self._clean_msg(msg))
    
    def log(self, *msg):
        self.logf.info(self._clean_msg(msg))
        print(self._clean_msg(msg))
    
    async def report(self, *msg):
        await self.send(*msg)
        self.logf.info(self._clean_msg(msg))
        print(self._clean_msg(msg))

def embed_contructor(**kwargs):
    """
    Accepted keyword arguments:
        title   = str | def:Empty
        url     = url(str) | def:Empty
        descr   = str | def:SPACE
        ts      = datetime | def:utcnow()
        author  = {'text': str, 'url': url(str) | def:Empty, 'icon': url(str) | def:Empty} | None
        colour  = list(3) | None
        thumb   = url(str)
        image   = url(str)
        footer  = {'text': str| def:None, 'url': str| def:None} | None
        fields  = [
            {
                'name'    = str | def:SPACE,
                'value'   = str | def:SPACE,
                'inline'  = bool | def:True
            }
        ]
    """
    embed = nextcord.Embed(
        title       = kwargs.get('title', EMPTY),
        url         = kwargs.get('url', EMPTY),
        description = kwargs.get('descr', EMPTY),
        timestamp   = kwargs.get('ts', dt.datetime.utcnow()),
        color       = nextcord.Colour.from_rgb(*kwargs['colour']) if kwargs.get('colour', False) else EMPTY
    )
    if kwargs.get('thumb', False):
        embed.set_thumbnail(url=kwargs['thumb'])

    if kwargs.get('footer', False):
        embed.set_footer(
            text=kwargs['footer']['text'], 
            icon_url=kwargs['footer']['url'] if kwargs['footer'].get('url', False) else EMPTY)
    
    if kwargs.get('image', False):
        embed.set_image(url=kwargs['image'])
    
    if kwargs.get('author', False):
        embed.set_author(
            name    = kwargs['author']['text'],
            url     = kwargs['author']['url'] if kwargs['author'].get('url', False) else EMPTY,
            icon_url= kwargs['author']['icon'] if kwargs['author'].get('icon', False) else EMPTY
        )
    
    for field in kwargs.get('fields', []):
        if isinstance(field, list):
            print(field)
            print(kwargs)
            raise Exception("WTF dood")

        embed.add_field(
            name    = field.get('name', SPACE),
            value   = field.get('value', SPACE),
            inline  = field.get('inline', True)
        )
    return embed

def process_input(s):
    """
    docstring
    """

    options = s.split(';')
    return options

class basePageHandler():
    def __init__(self, channel):
        self.channel = channel
        self.main_message = None

    async def send(self, **kwargs):
        return await self.channel.send(**kwargs)

    async def main_message_send(self, **kwargs):
        self.main_message = await self.send(**kwargs)
    
    async def update_message(self, **kwargs):
        await self.main_message.edit(**kwargs)

class baseViewHandler(nextcord.ui.View):
    def __init__(self, timeout:int):
        super().__init__(timeout=timeout)
    
    def load_items(self, items, **kwargs):
        if kwargs.get('reload', False): super().clear_items()
        for item in items:
            super().add_item(item)

    def pass_pageHandler(self, pageHandler):
        self.pageHandler = pageHandler

    #async def on_timeout()
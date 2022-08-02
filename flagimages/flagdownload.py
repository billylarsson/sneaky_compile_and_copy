from PIL import Image
import requests, json, time, os, tempfile

linux = os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind('/') + 1]
win = os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind('\\') + 1]

flaghtml = 'https://en.wikipedia.org/wiki/Gallery_of_sovereign_state_flags'
savepath = max([linux,win])
flaghtmlfile = f'{tempfile.gettempdir()}/flags.html'
jsonflagfile = f'{savepath}flags.json'
tmpfile = f'{tempfile.gettempdir()}/tmpflag.png'

class Cutouter:
    def __init__(self, contents, *args, **kwargs):
        self.org_contents = contents
        self.cache = None
        self.reset()
        self(*args, **kwargs)

    def __call__(self,

                    first_find=None,
                    find_first=None,
                    then_find=False,
                    start_from=False,
                    search_range=False,
                    preshrink=False,
                    plow=False,
                    rewind=0,
                    forward=0,
                    *args,
                    **kwargs,

                    ):

        self.plow_mode(plow)

        if find_first or first_find:
            self.set_starting_point(start_from)
            self.set_ending_point(search_range, preshrink)
            self.find_first_target(find_first or first_find, rewind, forward, search_range)

        if then_find:
            self.find_second_target(then_find)

    def __bool__(self):
        return self.status

    def __str__(self):
        if self.status:
            return self.text

    def reset(self):
        self.status, self.focus, self.back_focus = False, 0, -1

    def plow_mode(self, plow):
        """ will discard previous tracks as machine only plow forward, never backwards """
        if self.status and plow and max(self.focus, self.back_focus) > 0:
            self.org_contents = self.org_contents[max(self.focus, self.back_focus):]
            self.reset()

    def set_starting_point(self, start_from):
        """ set cache beginning, starting point will be fixed from here on """
        if start_from and len(self.org_contents) > start_from:
            self.cache = self.org_contents[start_from:]
        else:
            self.cache = self.org_contents

    def set_ending_point(self, search_range, preshrink=False):
        """ this only happens if first target has been discovered unless foreced """
        if search_range and len(self.cache) > search_range:
            if preshrink or self.focus > -1:

                if self.focus > -1:
                    self.cache = self.cache[self.focus:]
                    self.focus = 0

                if len(self.cache) > search_range:
                    self.cache = self.cache[0:search_range]

    def find_first_target(self, find_first, rewind=0, forward=0, search_range=False):
        if type(find_first) == str:
            find_first = [find_first]

        for query in find_first or []:

            self.status = False
            self.focus = self.cache[self.focus:].find(query) + self.focus

            if self.focus > -1:

                if type(rewind) == str:
                    self.focus += (0 - len(rewind))
                elif type(rewind) == bool and rewind:
                    self.focus += (0 - len(query))

                if type(forward) == str:
                    self.focus += len(forward)
                elif type(forward) == bool and forward:
                    self.focus += len(query)

                self.set_ending_point(search_range)

                self.text = self.cache[self.focus:]
                self.status = True
            else:
                return False

    def find_second_target(self, then_find):
        """then_find usually a string, but if its a list
        or tuple its a combined/additional first_find """
        if then_find and self.focus > -1:

            if type(then_find) == str:
                then_find = [then_find]

            for count, query in enumerate(then_find or []):
                self.status = False

                if count+1 < len(then_find):
                    self.find_first_target(query)  # backwards compatible
                    if not self.status:
                        return False
                else:
                    self.back_focus = self.cache[self.focus:].find(query) + self.focus

                    if self.back_focus > self.focus:
                        self.text = self.cache[self.focus:self.back_focus]
                        self.status = True
                    else:
                        return False

def download_index_and_make_json():
    flags = []

    if not os.path.exists(flaghtmlfile):
        rv = requests.get(flaghtml)
        if rv:
            with open(flaghtmlfile, 'w') as f:
                f.write(rv.content.decode())

    if not os.path.exists(flaghtmlfile):
        return flags

    with open(flaghtmlfile) as f:
        cont = f.read()

    co = Cutouter(cont, find_first='<')

    while co:

        flag = dict(country=None, url=None)

        co(first_find=['<li class="gallerybox"', 'src="//'], then_find='"', forward=True, plow=True)
        if co:
            flag['url'] = 'https://' + co.text

            co(first_find=['title="Flag of', '">'], then_find='</a>', forward=True)
            if co:
                flag['country'] = co.text

        if flag['country']:
            if os.path.exists(savepath + flag['country'] + '.webp'):
                flag['file'] = flag['country'] + '.webp'
            flags.append(flag)

    with open(jsonflagfile, 'w') as f:
        f.write(json.dumps(flags))

    return flags

def flagfile(country):
    flags = download_index_and_make_json()
    for i in flags:

        if i['country'].lower() != country.lower():
            continue

        webpfile = str(i['country']) + '.webp'

        if not os.path.exists(savepath + webpfile):
            rv = requests.get(i['url'])
            if rv:
                with open(tmpfile, 'wb') as f:
                    f.write(rv.content)

                im = Image.open(tmpfile)
                im.save(savepath + webpfile, 'webp', method=6, quality=70)

                print("Downloaded:", savepath + webpfile, os.path.getsize(savepath + webpfile), 'bytes')

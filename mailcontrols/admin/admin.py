import bottle
import traceback

from jinja2 import Template
from threading import Thread

filters = {}

@bottle.route("/")
def index():
    return "<html>" \
           "<body>" \
           "<a href='/filters'>Filters</a>" \
           "</body>" \
           "</html>"

@bottle.route("/filters")
def filter_list():
    global filters
    return Template(
            "<html>"
            "<body>"
            "<a href='/'>Home</a><br/><br/>"
            "{% for item in filters %}"
            "<a href='/filters/{{ item }}'>{{ item }}</a><br/>"
            "{% endfor %}"
            "</body>"
            "</html>"
        ).render(filters=filters.keys())

@bottle.route("/filters/<plugin>", method=["GET", "POST"])
def filter_admin(plugin):
    global filters
    if not plugin in filters.keys():
        return "Filter not found."
    else:
        try:
            return filters[plugin]['filter'].admin(params=bottle.request.params)
        except:
            return "<pre>" + traceback.format_exc() + "</pre>"


class interface(Thread):
    def __init__(self, filterindex):
        Thread.__init__(self)

        global filters
        filters = filterindex

        self.daemon = True

    def run(self):
        bottle.run(host='0.0.0.0', port=2525, quiet=True)


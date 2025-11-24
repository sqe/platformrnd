AUTHOR = 'Aziz Kurbanov'
SITENAME = 'Platform R&D'
SITEURL = 'https://sqe.github.io/platformrnd'

PATH = 'content'

TIMEZONE = 'America/Los_Angeles'
DEFAULT_LANG = 'en'

# Blog settings
DEFAULT_CATEGORY = 'Open Source Projects'
ARTICLE_URL = '{slug}.html'
ARTICLE_SAVE_AS = '{slug}.html'

# Static files, custom pages
STATIC_PATHS = ['images', 'extra/CNAME']
EXTRA_PATH_METADATA = {
    'extra/CNAME': {'path': 'CNAME'},
}

# Theme
THEME = 'theme'

# Plugins
PLUGINS = []

# Menu
DISPLAY_PAGES_ON_MENU = True
DISPLAY_CATEGORIES_ON_MENU = False

# Index page
INDEX_SAVE_AS = 'blog.html'

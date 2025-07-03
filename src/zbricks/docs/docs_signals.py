from zbricks.signals import Signal


class SiteConfigLoaded(Signal):
    path: str
    config: dict

class ContentDiscovered(Signal):
    content_dir: str
    files: list

class ContentLoaded(Signal):
    slug: str
    meta: dict
    body: str

class ThemeResolved(Signal):
    theme_dirs: list

class ServerStarted(Signal):
    host: str
    port: int

# You can add more signals/events as needed for extensibility.

import os
from telegram.ext import Updater
from lib.event_store import EventStore

# updater = Updater("1103896448:AAEPQ_zy2ftu4X23JYDO-fncx8rrxu2iXrI", use_context=True)
updater = Updater(os.environ["API_KEY"], use_context=True)

store = EventStore()
store.publish('connection', 'established', **{})

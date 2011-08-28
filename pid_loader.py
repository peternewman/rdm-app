# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# loader.py
# Copyright (C) 2011 Simon Newton
# The handlers for /pid /pid_search and /manufacturers

import logging
from model import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import data


class OutOfRangeException(Exception):
  """Raised when an enum valid isn't within the allowed ranges."""

class MissingItemsException(Exception):
  """Raised when an item is defined as a group, but no child items exist."""

class InvalidDataException(Exception):
  """Raised when the input data is invalid."""


class LoadHandler(webapp.RequestHandler):
  """Return the list of all manufacturers."""

  def AddItem(self, item):
    item_data = MessageItem(name = item['name'], type = item['type'])
    if item.get('min_size'):
      item_data.min_size = item['min_size']
    if item.get('max_size'):
      item_data.max_size = item['max_size']

    if item['type'] == 'group':
      items = item.get('items')
      if item.get('range') or item.get('enums'):
        raise InvalidDataException(
            '%s: groups cannot have enum or range properties' % item['name'])
      if item.get('multiplier'):
        raise InvalidDataException(
            '%s: groups cannot have multiplier properties' % item['name'])

      if not items:
        raise MissingItemsException(item['name'])

      child_items = []
      for child_item_data in items:
        child_item = self.AddItem(child_item_data)
        child_items.append(child_item.key())
      item_data.items = child_items


    valid_ranges = []
    if item.get('range'):
      ranges = []
      for min, max in item.get('range'):
        valid_ranges.append((min, max))
        range = AllowedRange(min = min, max = max)
        range.put()
        ranges.append(range.key())
      item_data.allowed_values = ranges

    if item.get('enums'):
      enums = []
      for value, label in item.get('enums'):
        if valid_ranges:
          found = False
          for min, max in valid_ranges:
            if value >= min and value <= max:
              break
          else:
            raise OutOfRangeException('%d: %s' % (value, label))

        enum = EnumValue(value = value, label = label)
        enum.put()
        enums.append(enum.key())
      item_data.enums = enums

    if item.get('multiplier'):
      item_data.multiplier = item['multiplier']

    item_data.put()
    return item_data

  def AddMessage(self, message):
    items = []
    for item in message['items']:
      items.append(self.AddItem(item).key())

    message_data = Message(items = items)
    message_data.put()
    return message_data

  def AddPid(self, pid, manufacturer_id = 0):
    manufacturer_q = Manufacturer.all()
    manufacturer_q.filter('esta_id =', manufacturer_id)
    manufacturer = manufacturer_q.fetch(1)[0]

    pid_data = Pid(manufacturer = manufacturer,
                   pid_id = pid['value'],
                   name = pid['name'])

    if pid.get('link'):
      pid_data.link = pid['link']
    elif manufacturer_id == 0:
      pid_data.link = 'http://tsp.plasa.org/tsp/documents/published_docs.php'


    if pid.get('notes'):
      pid_data.notes = pid['notes']

    if pid.get('get_request'):
      get_request = self.AddMessage(pid['get_request'])
      get_response = self.AddMessage(pid['get_response'])

      command = Command(sub_device_range = pid['get_sub_device_range'],
                        request = get_request,
                        response = get_response)
      command.put()
      pid_data.get_command = command

    logging.info(pid['name'])

    if pid.get('set_request'):
      set_request = self.AddMessage(pid['set_request'])
      set_response = self.AddMessage(pid['set_response'])

      command = Command(sub_device_range = pid['set_sub_device_range'],
                        request = set_request,
                        response = set_response)
      command.put()
      pid_data.set_command = command

    pid_data.put()



  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    for pid in data.pids:
      self.AddPid(pid)

    for manufacturer in data.manufacturers:
      for pid in manufacturer['pids']:
        self.AddPid(pid, manufacturer['id'])

    self.response.out.write('ok')


class ClearHandler(webapp.RequestHandler):
  """Return the list of all manufacturers."""
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    for item in MessageItem.all():
      item.delete()

    for item in Message.all():
      item.delete()

    for item in Command.all():
      item.delete()

    for item in Pid.all():
      item.delete()

    for item in EnumValue.all():
      item.delete()

    for item in AllowedRange.all():
      item.delete()

    self.response.out.write('ok')


application = webapp.WSGIApplication(
  [
    ('/load_p', LoadHandler),
    ('/clear_p', ClearHandler),
  ],
  debug=True)

def main():
  logging.getLogger().setLevel(logging.INFO)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

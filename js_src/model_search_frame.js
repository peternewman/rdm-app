/**
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * The Device Model Search Frame.
 * Copyright (C) 2011 Simon Newton
 */

goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.ui.AutoComplete.Basic');
goog.require('goog.ui.Component');
goog.require('goog.ui.CustomButton');

goog.require('app.Server');
goog.require('app.ModelTable');

goog.provide('app.ModelSearchFrame');


/**
 * Create a new device model search frame.
 * @constructor
 */
app.ModelSearchFrame = function(state_manager) {
  this._state_manager = state_manager;

  var t = this;
  this.manufacturer_search_input =
    goog.dom.$('device_model_manufacturer_input');
  goog.events.listen(
    goog.dom.$('device_model_form'),
    goog.events.EventType.SUBMIT,
    function(e) {
      e.stopPropagation();
      e.preventDefault();
      t.searchByManufacturer();
      return false;
    },
    false, this);
  var search_button = goog.dom.$('device_model_manufacturer_button');
  goog.ui.decorate(search_button);
  goog.events.listen(
      search_button,
      goog.events.EventType.CLICK,
      this.searchByManufacturer,
      false,
      this);

  // fire off a request to get the list of manufacturers
  var server = app.Server.getInstance();
  server.manufacturers(function(results) {t.newManufacturerList(results); });

  this.model_table = new app.ModelTable('device_model_table', state_manager);
};


/**
 * Setup an auto-complete based on the list of manufacturers.
 */
app.ModelSearchFrame.prototype.newManufacturerList = function(results) {
  if (results == undefined) {
    return;
  }

  var manufacturers = new Array();
  for (var i = 0; i < results['manufacturers'].length; ++i) {
    result = results['manufacturers'][i];
    manufacturers.push(
      result['name'] + ' [' + app.toHex(result['id'], 4) + ']');
  }
  var ac1 = new goog.ui.AutoComplete.Basic(
        manufacturers, this.manufacturer_search_input, false);
};


/**
 * Called when the product search button is clicked.
 */
app.ModelSearchFrame.prototype.searchByManufacturer = function() {
  var value = this.manufacturer_search_input.value;
  app.history.setToken('ps,' + value);
};


/**
 * Update the pid table with the new list of pids.
 */
app.ModelSearchFrame.prototype.newModels = function(models) {
  this.model_table.update(models);
};
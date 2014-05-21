#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import urllib2, os, logging, webapp2, random
#use logging.info("") to print stuff
from google.appengine.ext import webapp
from webapp2_extras import sessions
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from conf import USERNAME, PASSWORD
class Job(db.Model):
	title = db.StringProperty()
	link = db.StringProperty()
	notes = db.StringProperty()


class BaseHandler(webapp2.RequestHandler):
	def unset_session(self):
		self.session['loggedin'] = False

	def dispatch(self):
		self.session_store = sessions.get_store(request=self.request)
		try:
			webapp2.RequestHandler.dispatch(self)
		finally:
			self.session_store.save_sessions(self.response)

	@webapp2.cached_property
	def session(self):
		return self.session_store.get_session()

	def render_restricted_template(self, view_filename, params={}):
		if ('loggedin' in self.session and self.session['loggedin'] == True):
			self.render_template(view_filename, params)
		else:
			self.render_template('message.html', {'msg': 'Not Logged in.', 'login': True, 'Error': True})
		
	def render_template(self, view_filename, params={}):
		path = os.path.join(os.path.dirname(__file__), 'templates', view_filename)
		self.response.out.write(template.render(path, params))

class MainHandler(BaseHandler):
	def get(self):
		self.render_restricted_template('index.html', {})

class LoginHandler(BaseHandler):
	def get(self):
		self.render_template('message.html', {'msg': 'Not Logged in.', 'login': True, 'Error': True})
	def post(self):
		if self.request.get('username') == USERNAME and self.request.get('password') == PASSWORD:
			self.session['loggedin'] = True
			self.render_template('index.html', {'login': True})
		else:
			self.render_template('message.html', {'msg': 'Incorrect Credentials.', 'login': True, 'Error': True})

class LogoutHandler(BaseHandler):
    def get(self):
		self.session['loggedin'] = False
		self.render_template('message.html', {'msg': 'Successfully Logged Out.'})

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}
app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name='home'),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout')
], config=config, debug=True)
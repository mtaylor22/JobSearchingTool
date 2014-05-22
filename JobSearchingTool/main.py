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
from conf import USERS, SESSION_KEY
from google.appengine.ext.db import BadValueError

class Job(db.Model):
	title = db.StringProperty()
	link = db.LinkProperty()
	notes = db.TextProperty()
	location = db.StringProperty()
	compensation = db.StringProperty()
	user = db.StringProperty()

class BaseHandler(webapp2.RequestHandler):
	def unset_session(self):
		self.session['user'] = ""

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
		if ('user' in self.session and self.session['user'] != ""):
			self.render_template(view_filename, params)
		else:
			self.render_template('message.html', {'msg': 'Not Logged in.', 'login': True, 'Error': True})
		
	def render_template(self, view_filename, params={}):
		path = os.path.join(os.path.dirname(__file__), 'templates', view_filename)
		self.response.out.write(template.render(path, params))

class MainHandler(BaseHandler):
	def get(self):
		jobs = db.GqlQuery("SELECT * FROM Job WHERE user =:username", username=self.session['user'])
		jobs_wid = []
		for job in jobs:
			jobs_wid.append([job, job.key().id()])
		self.render_restricted_template('index.html', {'jobs': jobs_wid})

class ActionHandler(BaseHandler):
	def get(self):
		self.render_restricted_template('index.html', {})
	def post(self):
		#modify param value
		if self.request.get('action') == 'modify' and self.request.get('id') and self.request.get('param') and self.request.get('value'):
			job = Job.get_by_id(int(self.request.get('id')))
			setattr(job, self.request.get('param'), self.request.get('value'))
			job.put()
		self.render_restricted_template('index.html', {})

class AddJobHandler(BaseHandler):
	def get(self):
		self.render_restricted_template('index.html', {})
	def post(self):
		try:
			if self.request.get('link'):
				link = self.request.get('link')
			else:
				link = None
			job = Job(title=self.request.get('title'), link=link, notes=self.request.get('notes'), location=self.request.get('location'), compensation=self.request.get('compensation'), user=self.session['user'])
			job.put()
			self.render_restricted_template('index.html', {})
		except BadValueError:
			self.render_template('message.html', {'msg': 'Invalid Link', 'login': False, 'Error': True})


class LoginHandler(BaseHandler):
	def get(self):
		self.render_template('message.html', {'msg': 'Not Logged in.', 'login': True, 'Error': True})
	def post(self):
		if self.request.get('username') in USERS and USERS[self.request.get('username')] == self.request.get('password'):
			self.session['user'] = self.request.get('username')
			self.render_template('index.html', {'login': True})
		else:
			self.render_template('message.html', {'msg': 'Incorrect Credentials.', 'login': True, 'Error': True})

class LogoutHandler(BaseHandler):
    def get(self):
		self.session['user'] = ""
		self.render_template('message.html', {'msg': 'Successfully Logged Out.'})

config = {'webapp2_extras.sessions': {'secret_key': SESSION_KEY}}
app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name='home'),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout'),
    webapp2.Route('/action', ActionHandler, name='action'),
    webapp2.Route('/addjob', AddJobHandler, name='addjob')
], config=config, debug=True)
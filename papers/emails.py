# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals
from django.core.mail import send_mail
from papers.models import *
from datetime import datetime


#For now, I put a guard to prevent sending mail to any people except pintoch and bthom.
def send_email_for_paper(paper):
    allAuthors = paper.author_set.filter(researcher__isnull=False)	
    names = ", ".join(map(lambda x:x.name.full.title(),allAuthors)) 
    title = paper.title
    paper.date_last_ask = datetime.now().date() 
    url = "TODO, Url not available yet"
    my_template = open('papers/templates/papers/emailTemplate', 'r').read()
    fill_holes=my_template.replace('$NAMES', names).replace('$TITLE', title).replace('$URL',url)
    send_mail( "Someone is asking for one of your papers.", fill_holes , 'paper@dissem.in', list(set(["thomas.07fr@gmail.com","antonin@delpeuch.eu"])& set(map(lambda x: x.researcher.email,allAuthors))), fail_silently=False)
    paper.save()

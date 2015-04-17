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

#For now, I put a guard to prevent sending mail to any people except pintoch and bthom.
def send_email_for_paper(paper):
	allAuthors = paper.author_set.filter(researcher__isnull=False)	
	send_mail('Someone is asking for one of your papers', ", ".join(map(lambda x:x.name.full.title(),allAuthors)) + ",\n\n" +
	"Someone recently signaled on dissem.in that one of your papers is not available on a regular repository. "
	"However we believe the policy of the publisher does not forbid you to release a pre/post publication. \n\n"
	"The title of this paper is:\n" +
	paper.title  +
	"\n\nThat could be great if you could upload this paper! For that, you can use the following url, we already filled-up the"
	" metadatas so you just need the actual document. (URL AVAILABLE SOON) \n\n-----\ndissem.in"  
	, 'paper@dissem.in'
	, list(set(["thomas.07fr@gmail.com","antonin@delpeuch.eu"]) & set(map(lambda x: x.researcher.email,allAuthors)))
	, fail_silently=False)


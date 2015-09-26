{% load i18n %}
{% load statsurl %}
{"detailed":
  [
{ "label":"{% trans 'Available from the publisher' %}",
   "value":{{ stats.num_oa }},
   "url":"{{ object_id | statsurl:"oa" }}",
   "id": "oa"},
{ "label":"{% trans 'Available from the authors' %}",
   "value":{{ stats.num_ok }},
   "url":"{{ object_id | statsurl:"ok" }}",
   "id": "ok"},
{ "label":"{% trans 'Could be shared by the authors' %}",
  "value":"{{ stats.num_couldbe }}",
  "url": "{{ object_id | statsurl:"couldbe" }}",
  "id": "couldbe"},
{ "label":"{% trans 'Unknown sharing policy' %}",
  "value":{{ stats.num_unk }},
  "url": "{{ object_id | statsurl:"unk" }}",
  "id":"unk"},
{ "label":"{% trans 'Publisher forbids sharing' %}",
  "value":{{ stats.num_closed }},
  "url":"{{ object_id | statsurl:"closed" }}",
  "id":"closed"} ],
 "aggregated":
 [
    { "label":"{% trans 'Available' %}",
       "value":{{ stats.num_available }},
       "url":"{{ object_id | statsurl:"ok" }}" },
    { "label":"{% trans 'Unavailable' %}",
       "value":{{ stats.num_unavailable }},
       "url":"{{ object_id | statsurl:"nok" }}" }]
 }

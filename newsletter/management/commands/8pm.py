from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
#from optparse import make_option
from newsletter.models import Subscription,Newsletter,Message,List
import re

#this file imports users from leaked 8 Poznan Marathon List

class Command(BaseCommand):

    def import_auth_users(self, *args, **options):
        auth_list, created = List.objects.get_or_create(name="8pm_leak")
        file = open("newsletter/management/commands/runners.txt", "r")

        EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

        runners = []
        for email in file:
            if not EMAIL_REGEX.match(email):
                print "Error matching regex"
            else:
                runners.append(email.replace(',','').rstrip())

        users = []
        for u in User.objects.all():
            users.append(u.email)

        diff = [x for x in runners if x not in users]

        for u in diff:
            try:
                s = Subscription.objects.get(email_field=u)
                print "skipping, user alread loaded from auth: ",s
            except Subscription.DoesNotExist:
                print "adding new user from list intersection: ",u
                subscriber = Subscription(email_field=u,list=auth_list,subscribed=True)
                subscriber.save()

        print "Runners.txt len: ", len(runners)
        print "Current DB users len: ",len(users)
        print "Diff len: ",len(diff)

    def handle(self, *args, **options):
        return self.import_auth_users(*args,**options)

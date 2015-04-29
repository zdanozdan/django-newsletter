from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
#from optparse import make_option
from newsletter.models import Subscription,Newsletter,Message,List

class Command(BaseCommand):

    def import_auth_users(self, *args, **options):
        auth_list, created = List.objects.get_or_create(name="django_auth")
        users = User.objects.all()
        for u in users:
            try:
                s = Subscription.objects.get(user=u,list=auth_list)
                print "skipping, user alread loaded from auth: ",s
            except Subscription.DoesNotExist:
                print "adding new user from auth: ",u
                subscriber = Subscription(user=u,list=auth_list,subscribed=True)
                subscriber.save()

    def handle(self, *args, **options):
        return self.import_auth_users(*args,**options)

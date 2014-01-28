from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from optparse import make_option
from newsletter.models import Subscription,Newsletter,Message,List,Submission

class Command(BaseCommand):

    # Metadata about this command.
    option_list = BaseCommand.option_list + (
        make_option('--message', action='store', help='message name or pk'),
        make_option('--remove', action='store', help='remove submission'),
    )

    def handle(self, *args, **options):
        message_title = options.get('message')
        remove = options.get('remove')

        try:
            pk = int(message_title)
            message = Message.objects.get(id=pk)
        except:
            raise Exception("Messages object with ID: '%s' does not exists" % message_title)
            

        if remove:
            print "Remove submissions for message: ",message
            Submission.objects.filter(message=message).delete()
            exit()
            
        #build submission list
        subscriptions = Subscription.objects.filter(subscribed=True)
        for u in subscriptions:
            try:
                s = Submission.objects.get(subscription=u,message=message)
                print "skipping, user alread loaded for submission: ",s
            except Submission.DoesNotExist:
                print "adding new user for submisssion: ",u
                submission = Submission(subscription=u,message=message)
                submission.save()

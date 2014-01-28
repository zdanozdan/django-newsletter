from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template import Context, TemplateDoesNotExist
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.timezone import now

from optparse import make_option
from newsletter.models import Subscription,Newsletter,Message,List,Submission

class Command(BaseCommand):
    # Metadata about this command.
    option_list = BaseCommand.option_list + (
        make_option('--newsletter', action='store', help='newsletter name or pk'),
        make_option('--message', action='store', help='message name or pk'),
    )

    '''
    So here we need to pass newsletter name and message name or number (id) I guess
    Same newsletter can have multiple messages and each has identical rendering
    To change rendering new newsletter has to be created 
    '''
    def handle(self, *args, **options):
        newsletter_title = options.get('newsletter')
        message_title = options.get('message')

        try:
            pk = int(newsletter_title)
            newsletter = Newsletter.objects.get(id=pk)
        except Newsletter.DoesNotExist:   
            #print "Newsletter object with ID: '%s' does not exists" % newsletter_title
            raise Exception("Newsletter object with ID: '%s' does not exists" % newsletter_title)
        except:                        
            newsletter = Newsletter.objects.get(title=newsletter_title)

        print "Using newsletter: ", newsletter

        try:
            pk = int(message_title)
            message = Message.objects.get(id=pk,newsletter=newsletter)
        except Message.DoesNotExist:
            raise Exception("Messages object with ID: '%s' does not exists" % newsletter_title)
        except:
            message = Message.objects.get(newsletter=newsletter,title=message_title)
            

        print "Using message: ", message

        submissions = Submission.objects.filter(sent=False).filter(message=message)
        if not submissions:
            raise Exception("No more submitted adresses for sending.....")

        (subject_template, text_template, html_template) = newsletter.get_templates('message')

        if newsletter.test_mode:
            print "!!!!!!!!!!! Test mode, only 'newsletter_tester' group used !!!!!!!!!!!!!!!!!!!!!!!"
            submissions = Submission.objects.filter(subscription__user__groups__name='newsletter_tester').filter(message=message)
            print submissions
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

        for submission in submissions:
            '''
            First mark message as prepared
            '''
            submission.prepared=True
            submission.save()

            variable_dict = {
                'subscription': submission.subscription,
                'message': message,
                'newsletter': newsletter,
                'site': Site.objects.get_current(),
                'STATIC_URL': settings.STATIC_URL,
                'MEDIA_URL': settings.MEDIA_URL
                }

            unescaped_context = Context(variable_dict, autoescape=False)

            email_message = EmailMultiAlternatives(
                subject_template.render(unescaped_context),
                text_template.render(unescaped_context),
                from_email=newsletter.get_sender(),
                to=[submission.subscription.get_recipient()]
                )


            if html_template:
                escaped_context = Context(variable_dict)
                email_message.attach_alternative(html_template.render(escaped_context),"text/html")

            '''
            Now mark message as ready to send
            '''
            submission.sending=True
            submission.save()

            try:
                print "Sending mail to recipient: ",submission.subscription.get_recipient()
                email_message.send()
                '''
                Now mark message as ready to send
                '''
                submission.sent=True
                submission.sent_date = now()
                submission.save()
                    
            except Exception, e:
                # TODO: Test coverage for this branch.
                print e

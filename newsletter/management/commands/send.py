from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template import Context, TemplateDoesNotExist
from django.conf import settings

#from optparse import make_option
from newsletter.models import Subscription,Newsletter,Message

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    #option_list = BaseCommand.option_list + (
    #    make_option('--delete',
    #                action='store_true',
    #                dest='delete',
    #                default=False,
    #                help='Delete poll instead of closing it'),
    #    )

    def handle(self, *args, **options):
        print args
        #print options

        subscriptions = Subscription.objects.filter(subscribed=True)
        print subscriptions

        newsletter = Newsletter.objects.get(id=1)
        print newsletter
        message = Message.objects.get(newsletter=newsletter)
        print message

        (subject_template, text_template, html_template) = newsletter.get_templates('message')

        for subscription in subscriptions:
            variable_dict = {
                'subscription': subscription,
                #'site': Site.objects.get_current(),
                #'submission': self,
                'message': message,
                'newsletter': newsletter,
                #'date': self.publish_date,
                'STATIC_URL': settings.STATIC_URL,
                'MEDIA_URL': settings.MEDIA_URL
                }

            unescaped_context = Context(variable_dict, autoescape=False)

            message = EmailMultiAlternatives(
                subject_template.render(unescaped_context),
                text_template.render(unescaped_context),
                from_email=newsletter.get_sender(),
                to=[subscription.get_recipient()]
                )

            print "recipient: "
            print subscription.get_recipient()

            if html_template:
                escaped_context = Context(variable_dict)
                message.attach_alternative(html_template.render(escaped_context),"text/html")

                try:
                    print html_template.render(unescaped_context)
                    print "send disabled !!!!!!!!!!!!!1"
                    message.send()
                    
                except Exception, e:
                    # TODO: Test coverage for this branch.
                    print e

        #(subject_template, text_template, html_template) = self.message.newsletter.get_templates('message',self.message.lang)

        #if options['delete']:
        #    print "DELETE"
        #for poll_id in args:
        #    try:
        #        poll = Poll.objects.get(pk=int(poll_id))
        #    except Poll.DoesNotExist:
        #        raise CommandError('Poll "%s" does not exist' % poll_id)

        #    poll.opened = False
        #    poll.save()

#            self.stdout.write('Successfully closed poll "%s"' % poll_id)

import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.db.models import permalink

from django.template import Context, TemplateDoesNotExist
from django.template.loader import select_template, get_template

from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.timezone import now

from django.core.mail import EmailMultiAlternatives

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from django.conf import settings
from sorl.thumbnail import ImageField
from .utils import make_activation_code, get_default_sites

from tinymce.models import HTMLField

class Newsletter(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('newsletter title'))
    slug = models.SlugField(db_index=True, unique=True)
    email = models.EmailField(verbose_name=_('e-mail'), help_text=_('Sender e-mail'))
    sender = models.CharField(max_length=200, verbose_name=_('sender'), help_text=_('Sender name'))
    visible = models.BooleanField(default=True, verbose_name=_('visible'), db_index=True)
    test_mode = models.BooleanField(default=True, verbose_name=_('test'))

    def get_templates(self, action, lang='pl'):
        """
        Return a subject, text, HTML tuple with e-mail templates for
        a particular action. Returns a tuple with subject, text and e-mail
        template.
        """

        # Common substitutions for filenames
        template_subst = {
            'action': action,
            'newsletter': self.slug
            }

        assert action in [
            'subscribe', 'unsubscribe', 'update', 'message'
        ], 'Unknown action %s' % action

        # Common root path for all the templates
        template_root = 'newsletter/message/'
        # activate current translation for the message
        translation.activate(lang)

        subject_template = select_template([
            template_root + '%(newsletter)s/%(action)s_subject.txt' % template_subst,
            template_root + '%(action)s_subject.txt' % template_subst,
        ])

        text_template = select_template([
            template_root + '%(newsletter)s/%(action)s.txt' % template_subst,
            template_root + '%(action)s.txt' % template_subst,
        ])

        html_template = self.get_html_template()

        return (subject_template, text_template, html_template)

    def get_html_template(self,action="message", template_root='newsletter/message/'):

        # Common substitutions for filenames
        template_subst = {
            'action': action,
            'newsletter': self.slug
            }

        try:
            html_template = select_template([
                template_root + '%(newsletter)s/%(action)s.html' % template_subst,
                template_root + '%(action)s.html' % template_subst,
            ])
        except TemplateDoesNotExist:
            # HTML templates are not required
            html_template = None

        return html_template
        

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('newsletter')
        verbose_name_plural = _('newsletters')

    @permalink
    def get_absolute_url(self):
        return (
            'newsletter_detail', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def subscribe_url(self):
        return (
            'newsletter_subscribe_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def unsubscribe_url(self):
        return (
            'newsletter_unsubscribe_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def update_url(self):
        return (
            'newsletter_update_request', (),
            {'newsletter_slug': self.slug}
        )

    @permalink
    def archive_url(self):
        return (
            'newsletter_archive', (),
            {'newsletter_slug': self.slug}
        )

    def get_sender(self):
        return u'%s <%s>' % (self.sender, self.email)

    def get_subscriptions(self):
        logger.debug(u'Looking up subscribers for %s', self)

        return Subscription.objects.filter(newsletter=self, subscribed=True)

    @classmethod
    def get_default_id(cls):
        try:
            objs = cls.objects.all()
            if objs.count() == 1:
                return objs[0].id
        except:
            pass
        return None

class List(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True, verbose_name=_('name'))

    def __unicode__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('user'))
    name_field = models.CharField(db_column='name', max_length=30, blank=True, null=True, verbose_name=_('name, club or nick'), help_text=_('optional'))
    email_field = models.EmailField(db_column='email', verbose_name=_('e-mail'), db_index=True, blank=True, null=True )
    ip = models.IPAddressField(_("IP address"), blank=True, null=True)
    #newsletter = models.ForeignKey('Newsletter', verbose_name=_('newsletter'))
    list = models.ForeignKey(List, default=lambda: List.objects.get(id=1), verbose_name=_('list'))
    create_date = models.DateTimeField(editable=False, default=now)
    activation_code = models.CharField(verbose_name=_('activation code'), max_length=40,default=make_activation_code )
    subscribed = models.BooleanField(default=False, verbose_name=_('subscribed'), db_index=True)
    subscribe_date = models.DateTimeField(verbose_name=_("subscribe date"), null=True, blank=True)

    # This should be a pseudo-field, I reckon.
    unsubscribed = models.BooleanField(default=False, verbose_name=_('unsubscribed'), db_index=True)
    unsubscribe_date = models.DateTimeField(verbose_name=_("unsubscribe date"), null=True, blank=True)

    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        unique_together = ('user', 'email_field')

    def get_name(self):
        if self.user:
            return self.user
            #return self.user.get_full_name()
        return self.name_field

    def set_name(self, name):
        if not self.user:
            self.name_field = name
    name = property(get_name, set_name)

    def get_email(self):
        if self.user:
            return self.user.email
        return self.email_field

    def set_email(self, email):
        if not self.user:
            self.email_field = email
    email = property(get_email, set_email)

    def subscribe(self):
        logger.debug(u'Subscribing subscription %s.', self)

        self.subscribe_date = now()
        self.subscribed = True
        self.unsubscribed = False

    def unsubscribe(self):
        logger.debug(u'Unsubscribing subscription %s.', self)

        self.subscribed = False
        self.unsubscribed = True
        self.unsubscribe_date = now()

    def save(self, *args, **kwargs):

        #check if user exists in DB
        try:
            self.user = User.objects.get(email__exact=self.email_field)
            self.email_field = None
            self.name_field = None
        except:
            pass

        assert self.user or self.email_field, \
            _('Neither an email nor a username is set. This asks for '
              'inconsistency!')
        assert ((self.user and not self.email_field) or
                (self.email_field and not self.user)), \
            _('If user is set, email must be null and vice versa.')


        # This is a lame way to find out if we have changed but using Django
        # API internals is bad practice. This is necessary to discriminate
        # from a state where we have never been subscribed but is mostly for
        # backward compatibility. It might be very useful to make this just
        # one attribute 'subscribe' later. In this case unsubscribed can be
        # replaced by a method property.

        if self.pk:
            assert(Subscription.objects.filter(pk=self.pk).count() == 1)

            subscription = Subscription.objects.get(pk=self.pk)
            old_subscribed = subscription.subscribed
            old_unsubscribed = subscription.unsubscribed

            # If we are subscribed now and we used not to be so, subscribe.
            # If we user to be unsubscribed but are not so anymore, subscribe.
            if ((self.subscribed and not old_subscribed) or
               (old_unsubscribed and not self.unsubscribed)):
                self.subscribe()

                assert not self.unsubscribed
                assert self.subscribed

            # If we are unsubcribed now and we used not to be so, unsubscribe.
            # If we used to be subscribed but are not subscribed anymore,
            # unsubscribe.
            elif ((self.unsubscribed and not old_unsubscribed) or
                  (old_subscribed and not self.subscribed)):
                self.unsubscribe()

                assert not self.subscribed
                assert self.unsubscribed
        else:
            if self.subscribed:
                self.subscribe()
            elif self.unsubscribed:
                self.unsubscribe()

        super(Subscription, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.name:
            return _(u"%(name)s <%(email)s> to list <%(list)s>") % {
                'name': self.name,
                'email': self.email,
                'list': self.list
            }

        else:
            return _(u"%(email)s to newsletter <%(list)s>") % {
                'email': self.email,
                'list': self.list
            }

    def get_recipient(self):
        if self.name:
            return u'%s <%s>' % (self.name, self.email)

        return u'%s' % (self.email)

    def send_activation_email(self, action, lang="pl"):

        assert action in [
            'subscribe', 'unsubscribe', 'update'
        ], 'Unknown action'

        # Common root path for all the templates
        template_root = 'newsletter/message/'
        # activate current translation for the message
        translation.activate(lang)

        subject_template = get_template(template_root + '%s_subject.txt' % action)
        text_template = get_template(template_root + '%s.txt' % action)

        try:
            html_template = get_template(
                template_root + '%s.html' % action,
            )
        except TemplateDoesNotExist:
            # HTML templates are not required
            html_template = None


        variable_dict = {
            'subscription': self,
            'date': self.subscribe_date,
            'site': Site.objects.get_current(),
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL
        }

        unescaped_context = Context(variable_dict, autoescape=False)

        message = EmailMultiAlternatives(
            subject_template.render(unescaped_context),
            text_template.render(unescaped_context),
            #from_email=self.newsletter.get_sender(),
            #from_email="enduhub",
            to=[self.email]
        )

        if html_template:
            escaped_context = Context(variable_dict)
            message.attach_alternative(html_template.render(escaped_context),"text/html")

        message.send()

        logger.debug(
            u'Activation email sent for action "%(action)s" to %(subscriber)s '
            u'with activation code "%(action_code)s".', {
                'action_code': self.activation_code,
                'action': action,
                'subscriber': self
            }
        )

    @permalink
    def subscribe_activate_url(self):
        return ('newsletter_update_activate', (), {
            'email': self.email,
            'action': 'subscribe',
            'activation_code': self.activation_code
        })

    @permalink
    def unsubscribe_activate_url(self):
        return ('newsletter_update_activate', (), {
            'email': self.email,
            'action': 'unsubscribe',
            'activation_code': self.activation_code
        })

    @permalink
    def update_activate_url(self):
        return ('newsletter_update_activate', (), {
            'email': self.email,
            'action': 'update',
            'activation_code': self.activation_code
        })

class Message(models.Model):
    TEMPLATES = ( ('newsletter/message/', 'newsletter/message/'), )

    title = models.CharField(max_length=200, verbose_name=_('title'))
    slug = models.SlugField(verbose_name=_('slug'), max_length=200)
    lang = models.CharField(verbose_name=_(u"language"), max_length=4, choices=settings.LANGUAGES, default='pl')
    url = models.URLField(verbose_name=_('link'), blank=True, null=True)
    text = HTMLField(verbose_name=_("text"))
    #plain_text = models.TextField(blank=True, verbose_name=_("text"))
    newsletter = models.ForeignKey('Newsletter', verbose_name=_('newsletter'),default=Newsletter.get_default_id)
    active = models.BooleanField(default=False, verbose_name=_('active'))
    image = ImageField(upload_to='newsletter/images/%Y/%m/%d', blank=True, null=True,verbose_name=_('image'))
    template_root = models.CharField(max_length=100, verbose_name=_('template path'), choices=TEMPLATES, default='newsletter/message/')
    date_create = models.DateTimeField(verbose_name=_('created'), auto_now_add=True, editable=False)
    date_modify = models.DateTimeField(verbose_name=_('modified'), auto_now=True, editable=False)

    def __unicode__(self):
        try:
            return _(u"%(title)s in %(newsletter)s") % {
                'title': self.title,
                'newsletter': self.newsletter
            }
        except Newsletter.DoesNotExist:
            logger.warn(
                'Database inconsistency, related newsletter not found '
                'for message with id %d', self.id
            )

            return "%s" % self.title

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        unique_together = ('slug', 'newsletter')

    @classmethod
    def get_default_id(cls):
        try:
            objs = cls.objects.all().order_by('-date_create')
            if not objs.count() == 0:
                return objs[0].id
        except:
            pass

        return None

import logging

logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse,resolve
from django.conf import settings

from django.template.response import SimpleTemplateResponse
from django.template import RequestContext

from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotFound

from django.views.generic import (
    ListView, DetailView,
    ArchiveIndexView, DateDetailView,
    TemplateView, FormView
)

from django.contrib import messages
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required

from django.utils.decorators import method_decorator
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import translation

from django.forms.models import modelformset_factory

from .models import Newsletter, Subscription, Message
from .forms import ( SubscribeRequestForm, UserUpdateForm, UpdateRequestForm, UnsubscribeRequestForm, UpdateForm )
from .tables import MessagesTable
from django_tables2 import RequestConfig

'''Simple views go here '''

def newsletter_list(request):
    qs = Message.objects.filter(active=True).order_by('-date_create')
    table = MessagesTable(qs)

    try:
        u,created = Subscription.objects.get_or_create(user=request.user)
        f =  UserUpdateForm
    except:
        u = None
        f = SubscribeRequestForm

    form = f(instance=u)

    if request.method == 'POST':
        form = f(request.POST, instance=u)
        if form.is_valid():
            # Everything's allright, let's save
            form.save()
            subscription = form.instance

            if not u:
                #activate language
                lang = translation.get_language()
                subscription.send_activation_email(action=request.POST.get('action'),lang=lang)
                messages.add_message(request,messages.SUCCESS, _(u'Please check your email and follow given link to confirm.'))
            else:
                messages.add_message(request,messages.SUCCESS, _(u'Your changes have been saved.'))

            return HttpResponseRedirect(reverse('newsletter_list'))

    RequestConfig(request,paginate={'per_page':25}).configure(table)
    return render_to_response('newsletter/message_list.html', {
            'table': table,
            'form': form,
            },context_instance=RequestContext(request))
    

def newsletter_detail(request,newsletter_slug):
    qs = Message.objects.filter(active=True).order_by('-date_create')
    table = MessagesTable(qs)
    m = qs.get(slug=newsletter_slug)

    try:
        u = Subscription.objects.get(user=request.user)
        f =  UserUpdateForm
    except:
        u = None
        f = SubscribeRequestForm

    form = f(instance=u)

    RequestConfig(request,paginate={'per_page':25}).configure(table)
    return render_to_response('newsletter/message_detail.html', {
            'table': table,
            'form': form,
            'message': m,
            },context_instance=RequestContext(request))

class NewsletterViewBase(object):
    """ Base class for newsletter views. """
    queryset = Message.objects.filter(active=True)
    allow_empty = False

    def get_object(self, queryset=None):  
        # This is a workaround for Django 1.3 and should be replaced by
        # the `slug_url_kwarg = 'newsletter_slug'` view attribute as soon
        # as 1.3 support is dropped.
        #self.kwargs['slug'] = self.kwargs['newsletter_slug']
        return self.queryset.get(slug=self.kwargs['newsletter_slug'])

class NewsletterDetailView(NewsletterViewBase, DetailView):
    context_object_name = "news_message"

    def get_form(self):
        try:
            u = Subscription.objects.get(user=self.request.user)            
            return UserUpdateForm(instance=u)
        except:
            return SubscribeRequestForm()

    def get_context_data(self, **kwargs):
        context = super(NewsletterDetailView, self).get_context_data(**kwargs)
        qs = Message.objects.filter(active=True).order_by('-date_create')
        context['table'] = MessagesTable(qs)
        context['form'] = self.get_form()
        return context


class MessageDetailView(NewsletterViewBase, DetailView):
    pass

class NewsletterListView(NewsletterViewBase, ListView):
    """
    List available newsletters and generate a formset for (un)subscription for
    authenticated users.
    """

    def post(self, request, **kwargs):
        """ Allow post requests. """

        # All logic (for now) occurs in the form logic
        return super(NewsletterListView, self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NewsletterListView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            # Add a formset for logged in users.
            context['form'] = self.get_form()

        return context

    def get_form(self):
        """ Return a formset with newsletters for logged in users, or None. """

        # Short-hand variable names
        newsletters = self.get_queryset()
        request = self.request
        user = request.user

        #SubscriptionFormSet = modelformset_factory(Subscription, form=UserUpdateForm, extra=0)
        #form = UserUpdateForm

        # Before rendering the formset, subscription objects should
        # already exist.
        #for n in newsletters:
        #    Subscription.objects.get_or_create(user=user)

        # Get  subscription for use in the form
        u = Subscription.objects.get( user=user )

        if request.method == 'POST':
            try:
                form = UserUpdateForm(request.POST,instance=u)

                if not form.is_valid():
                    raise ValidationError('Update form invalid.')

                # Everything's allright, let's save
                form.save()
                messages.info(request,ugettext("Your changes have been saved."))

            except ValidationError:
                # Invalid form posted. As there is no way for a user to
                # enter data - invalid forms should be ignored from the UI.

                # However, we log them for debugging purposes.
                logger.warning('Invalid form post received',
                    exc_info=True, extra={'request': request})

                # Present a pristine form
                form = UserUpdateForm(instance=u)

        else:
            form = UserUpdateForm(instance=u)

        return form


class NewsletterMixin(object):
    """ Mixin providing the ability to retrieve a newsletter. """

    def get_newsletter(self,newsletter_slug=None, newsletter_queryset=None, **kwargs):
        """
        Return the newsletter for the current request.

        By default this requires a `newsletter_slug` argument in the URLconf.
        """

        if newsletter_slug is None:
            assert 'newsletter_slug' in self.kwargs
            newsletter_slug = self.kwargs['newsletter_slug']

        if newsletter_queryset is None:
            newsletter_queryset = Newsletter.objects.all()

        newsletter = get_object_or_404(
            newsletter_queryset, slug=newsletter_slug,
        )

        return newsletter

    def get_form_kwargs(self):
        """ Add newsletter to form kwargs. """
        kwargs = super(NewsletterMixin, self).get_form_kwargs()

        #kwargs['newsletter'] = self.newsletter

        return kwargs

    def get_context_data(self, **kwargs):
        """ Add newsletter to context. """
        context = super(NewsletterMixin, self).get_context_data(**kwargs)

        #context['newsletter'] = self.newsletter

        return context


class ActionUserView(NewsletterMixin, TemplateView):
    """ Base class for subscribe and unsubscribe user views. """
    action = None

    def get_context_data(self, **kwargs):
        """ Add action to context. """
        context = super(ActionUserView, self).get_context_data(**kwargs)

        context['action'] = self.action

        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.newsletter = self.get_newsletter(**kwargs)

        # confirm is optional kwarg defaulting to False
        self.confirm = kwargs.get('confirm', False)

        return super(ActionUserView, self).dispatch(*args, **kwargs)


class SubscribeUserView(ActionUserView):
    action = 'subscribe'
    template_name = "newsletter/subscription_subscribe_user.html"

    def get(self, request, *args, **kwargs):
        already_subscribed = False
        instance = Subscription.objects.get_or_create(user=request.user)[0]

        if instance.subscribed:
            already_subscribed = True
        elif self.confirm:
            instance.subscribed = True
            instance.save()

            messages.success(
                request,
                _('You have been subscribed to %s.') % self.newsletter
            )

            logger.debug(
                _('User %(rs)s subscribed to %(my_newsletter)s.'), {
                    "rs": request.user,
                    "my_newsletter": self.newsletter
            })

        if already_subscribed:
            messages.info(
                request,
                _('You are already subscribed to %s.') % self.newsletter
            )

        return super(SubscribeUserView, self).get(request, *args, **kwargs)


class UnsubscribeUserView(ActionUserView):
    action = 'unsubscribe'
    template_name = "newsletter/subscription_unsubscribe_user.html"

    def get(self, request, *args, **kwargs):
        not_subscribed = False

        try:
            instance = Subscription.objects.get(user=request.user)

            if not instance.subscribed:
                not_subscribed = True
            elif self.confirm:
                instance.subscribed = False
                instance.save()

                messages.success(request,_('You have been unsubscribed from %s.') % self.newsletter)

                logger.debug(
                    _('User %(rs)s unsubscribed from %(my_newsletter)s.'), {
                        "rs": request.user,
                        "my_newsletter": self.newsletter
                })

        except Subscription.DoesNotExist:
            not_subscribed = True

        if not_subscribed:
            messages.info(request,
                _('You are not subscribed to %s.') % self.newsletter)

        return super(UnsubscribeUserView, self).get(request, *args, **kwargs)


class ActionRequestView(NewsletterMixin, FormView):
    """ Base class for subscribe, unsubscribe and update request views. """
    action = None

    def get_context_data(self, **kwargs):
        """ Add error and action to context. """
        context = super(ActionRequestView, self).get_context_data(**kwargs)

        context.update({
            'error': self.error,
            'action': self.action
        })

        return context

    def get_subscription(self, form):
        """ Return subscription for the current request. """
        return form.instance

    def form_valid(self, form):
        subscription = self.get_subscription(form)

        try:
            subscription.send_activation_email(action=self.action)

        except Exception, e:
            logger.exception('Error %s while submitting email to %s.',
                e, subscription.email)
            self.error = True

        return self.render_to_response(self.get_context_data(form=form))

    def dispatch(self, *args, **kwargs):
        self.newsletter = self.get_newsletter(**kwargs)
        self.error = None

        return super(ActionRequestView, self).dispatch(*args, **kwargs)


class SubscribeRequestView(ActionRequestView):
    action = 'subscribe'
    form_class = SubscribeRequestForm
    template_name = "newsletter/subscription_subscribe.html"
    confirm = False

    def get_form_kwargs(self):
        """ Add ip to form kwargs for submitted forms. """
        kwargs = super(SubscribeRequestView, self).get_form_kwargs()

        if self.request.method in ('POST', 'PUT'):
            kwargs['ip'] = self.request.META.get('REMOTE_ADDR')

        return kwargs

    def get_subscription(self, form):
        return form.save()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            kwargs['confirm'] = self.confirm
            return SubscribeUserView.as_view()(request, *args, **kwargs)

        return super(SubscribeRequestView, self).dispatch(
            request, *args, **kwargs
        )


class UnsubscribeRequestView(ActionRequestView):
    action = 'unsubscribe'
    form_class = UnsubscribeRequestForm
    template_name = "newsletter/subscription_unsubscribe.html"
    confirm = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            kwargs['confirm'] = self.confirm
            return UnsubscribeUserView.as_view()(request, *args, **kwargs)

        return super(UnsubscribeRequestView, self).dispatch(
            request, *args, **kwargs
        )


class UpdateRequestView(ActionRequestView):
    action = 'update'
    form_class = UpdateRequestForm
    template_name = "newsletter/subscription_update.html"


class UpdateSubscriptionViev(NewsletterMixin, FormView):
    form_class = UpdateForm
    template_name = "newsletter/subscription_activate.html"

    def get_initial(self):
        """ Returns the initial data to use for forms on this view. """
        if self.activation_code:
            return {'user_activation_code': self.activation_code}
        else:
            # TODO: Test coverage of this branch
            return None

    def get_form_kwargs(self):
        """ Add instance to form kwargs. """
        kwargs = super(UpdateSubscriptionViev, self).get_form_kwargs()

        kwargs['instance'] = self.subscription

        return kwargs

    def get_context_data(self, **kwargs):
        """ Add action to context. """
        context = \
            super(UpdateSubscriptionViev, self).get_context_data(**kwargs)

        context['action'] = self.action

        return context

    def form_valid(self, form):
        # Get our instance, but do not save yet
        subscription = form.save(commit=False)

        # If a new subscription or update, make sure it is subscribed
        # Else, unsubscribe
        if self.action == 'subscribe' or self.action == 'update':
            subscription.subscribed = True
        else:
            subscription.unsubscribed = True

        logger.debug(
            _(u'Updated subscription %(subscription)s through the web.'),
            {'subscription': subscription}
        )
        subscription.save()

        return self.render_to_response(self.get_context_data(form=form))

    def dispatch(self, *args, **kwargs):
        assert 'action' in kwargs
        assert 'email' in kwargs

        self.action = kwargs['action']
        assert self.action in ['subscribe', 'update', 'unsubscribe']

        #self.newsletter = self.get_newsletter(**kwargs)
        self.subscription = get_object_or_404(
            Subscription,
            email_field__exact=kwargs['email']
        )
        # activation_code is optional kwarg which defaults to None
        self.activation_code = kwargs.get('activation_code')

        return super(UpdateSubscriptionViev, self).dispatch(*args, **kwargs)


class SubmissionViewBase(NewsletterMixin):
    """ Base class for submission archive views. """
    date_field = 'publish_date'
    allow_empty = True
    #queryset = Submission.objects.filter(publish=True)
    slug_field = 'message__slug'

    # Specify date element notation
    year_format = '%Y'
    month_format = '%m'
    day_format = '%d'

    def get(self, request, *args, **kwargs):
        # Make sure newsletter is available for further processing
        self.newsletter = self.get_newsletter(
            newsletter_queryset=NewsletterListView().get_queryset()
        )

        return super(SubmissionViewBase, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """ Filter out submissions for current newsletter. """
        qs = super(SubmissionViewBase, self).get_queryset()

        qs = qs.filter(newsletter=self.newsletter)

        return qs


class SubmissionArchiveIndexView(SubmissionViewBase, ArchiveIndexView):
    pass


class SubmissionArchiveDetailView(SubmissionViewBase, DateDetailView):
    def get_context_data(self, **kwargs):
        """
        Make sure the actual message is available.
        """
        context = \
            super(SubmissionArchiveDetailView, self).get_context_data(**kwargs)

        message = self.object.message

        context.update({
            'message': message,
            'site': Site.objects.get_current(),
            'date': self.object.publish_date,
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL
        })

        return context

    def get_template(self):
        """ Get the message template for the current newsletter. """

        (subject_template, text_template, html_template) = \
            self.object.newsletter.get_templates('message')

        # No HTML -> no party!
        if not html_template:
            raise Http404(ugettext('No HTML template associated with the '
                                   'newsletter this message belongs to.'))

        return html_template

    def render_to_response(self, context, **response_kwargs):
        """
        Return a simplified response; the template should be rendered without
        any context. Use a SimpleTemplateResponse as a RequestContext should
        not be used.
        """
        return SimpleTemplateResponse(
            template=self.get_template(),
            context=context,
            **response_kwargs
        )

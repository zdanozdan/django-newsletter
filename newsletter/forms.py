from django.utils.translation import ugettext_lazy as _

from django import forms
from django.forms.util import ValidationError

from django.contrib.auth.models import User

from .models import Subscription,Message

class NewsletterForm(forms.ModelForm):
    """ This is the base class for all forms managing subscriptions. """

    email_field = forms.CharField(required=True, label=_("Email"))

    class Meta:
        model = Subscription
        fields = ('name_field', 'email_field')

    def __init__(self, *args, **kwargs):

        if 'ip' in kwargs:
            ip = kwargs['ip']
            del kwargs['ip']
        else:
            ip = None

        super(NewsletterForm, self).__init__(*args, **kwargs)
        #if self.instance:            
        #    self.fields[''] = forms.CharField()
        
        if ip:
            self.instance.ip = ip


class SubscribeRequestForm(NewsletterForm):
    """
    Request subscription to the newsletter. Will result in an activation email
    being sent with a link where one can edit, confirm and activate one's
    subscription.
    """

    ACTIONS = (
        ('subscribe', _(u'subscribe')),
        ('unsubscribe', _(u'unsubscribe')),
        )

    action = forms.ChoiceField(widget=forms.widgets.RadioSelect, choices=ACTIONS,label=_('action'), initial='subscribe')

    def clean(self):
        try:
            email = self.cleaned_data['email_field']
            action = self.cleaned_data['action']
        except:
            email = None
            action = None

        try:
            action = self.cleaned_data['action']
        except:
            action = None

        try:
            subscription = Subscription.objects.get(email_field__exact=email)
            self.instance = subscription
        except Subscription.DoesNotExist:
            subscription = None

        if action=="subscribe":
            if subscription is not None:
                if subscription.subscribed and not subscription.unsubscribed:
                    raise ValidationError(_("Your e-mail address has already been subscribed to."))
        elif action=="unsubscribe":
            if subscription is None:
                raise ValidationError(_("Your e-mail address has not been subscribed to."))
            elif subscription.unsubscribed and not subscription.subscribed:
                raise ValidationError(_("Your e-mail address has already been unsubscribed from."))
        else:
            raise ValidationError(_("Invalid subscription option"))

        return self.cleaned_data

    def clean_email_field(self):
        try:
            data = self.cleaned_data['email_field']
        except:
            raise ValidationError(_("An e-mail address is required."))

        # Check whether we should be subscribed to as a user
        try:
            user = User.objects.get(email__exact=data)

            raise ValidationError(_(
                "The e-mail address '%(email)s' belongs to a user with an "
                "account on this site. Please log in as that user "
                "and try again."
            ) % {'email': user.email})

        except User.DoesNotExist:
            pass

        # Check whether we have already been subscribed to
        #try:
        #    subscription = Subscription.objects.get(email_field__exact=data)

            #if subscription.subscribed and not subscription.unsubscribed:
            #    raise ValidationError(_("Your e-mail address has already been subscribed to."))
            #else:
            #    self.instance = subscription

        #    self.instance = subscription

        #except Subscription.DoesNotExist:
        #    pass

        return data


class UpdateRequestForm(NewsletterForm):
    """
    Request updating or activating subscription. Will result in an activation
    email being sent.
    """

    class Meta(NewsletterForm.Meta):
        fields = ('email_field',)

    def clean(self):
        if not self.instance.subscribed:
            raise ValidationError(
                _("This subscription has not yet been activated.")
            )

        return super(UpdateRequestForm, self).clean()

    def clean_email_field(self):
        data = self.cleaned_data['email_field']

        if not data:
            raise ValidationError(_("An e-mail address is required."))

        # Check whether we should update as a user
        try:
            user = User.objects.get(email__exact=data)

            raise ValidationError(
                _("This e-mail address belongs to the user '%(username)s'. "
                  "Please log in as that user and try again.")
                % {'username': user.username}
            )

        except User.DoesNotExist:
            pass

        # Set our instance on the basis of the email field, or raise
        # a validationerror
        try:
            self.instance = Subscription.objects.get(email_field__exact=data)

        except Subscription.DoesNotExist:
                raise ValidationError(_("This e-mail address has not been subscribed to."))

        return data


class UnsubscribeRequestForm(UpdateRequestForm):
    """
    Similar to previous form but checks if we have not
    already been unsubscribed.
    """

    def clean(self):
        if self.instance.unsubscribed:
            raise ValidationError(
                _("This subscription has already been unsubscribed from.")
            )

        return super(UnsubscribeRequestForm, self).clean()


class UpdateForm(NewsletterForm):
    """
    This form allows one to actually update to or unsubscribe from the
    newsletter. To do this, a correct activation code is required.
    """
    def clean_user_activation_code(self):
        data = self.cleaned_data['user_activation_code']

        if data != self.instance.activation_code:
            raise ValidationError(
                _('The validation code supplied by you does not match.')
            )

        return data

    user_activation_code = forms.CharField(label=_("Activation code"), max_length=40 )


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating subscription information/unsubscribing as a logged-in
    user.
    """

    class Meta:
        model = Subscription
        fields = ('subscribed',)
        # Newsletter here should become a read only field,
        # once this is supported by Django.

        # For now, use a hidden field.
        #hidden_fields = ('email',)

from django.contrib import admin
from chat.models import Message, Thread, Notification

from django.contrib.auth import get_user_model


User = get_user_model()


class MessageInline(admin.StackedInline):
    model = Message
    fields = ('sender', 'text')
    readonly_fields = ('sender', 'text')


class ThreadAdmin(admin.ModelAdmin):
    model = Thread
    inlines = (MessageInline,)

admin.site.register(Thread, ThreadAdmin)

admin.site.register(User)
admin.site.register(Notification)

admin.site.register(Message)
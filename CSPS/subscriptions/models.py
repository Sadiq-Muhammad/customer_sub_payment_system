from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=15)
    subscription_expiry = models.DateField()
    is_logged_in = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

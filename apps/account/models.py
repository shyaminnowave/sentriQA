from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Account(AbstractUser,):

    email = models.EmailField(unique=True, max_length=255, db_index=True)
    
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        db_table = 'auth_account'
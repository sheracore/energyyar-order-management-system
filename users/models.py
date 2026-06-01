from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.IntegerChoices):
    ADMIN = 1, 'Admin'
    CUSTOMER = 2, 'Customer'


class User(AbstractUser):
    role = models.IntegerField(
        choices=Role.choices,
        default=Role.CUSTOMER
    )

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_customer(self):
        return self.role == Role.CUSTOMER

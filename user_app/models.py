from django.db import models
import re

# Create your models here.
class UserManager(models.Manager):
    def validate_new_user(self, user_data):
        errors = {}

        if len(user_data["username"]) < 3:
            errors["username"] = "Username must be at least 3 characters."
        if len(user_data["password"]) < 7:
            errors["password"] = "Password must be at least 8 characters."
        if user_data["password"] != user_data["confirm_password"]:
            errors["confirm_password"] = "Passwords must match."

        # Test if username is already taken
        if len(User.objects.filter(username=user_data["username"])) > 0:
            errors["username"] = "That username has already been taken!"

        # Test for password validations
        if not re.findall("[0-9]", user_data["password"]):
            errors["password_digit"] = "Password must contain at least 1 digit."
        if not re.findall("[^\w\s]", user_data["password"]):
            errors["password_special"] = "Password must contain at least 1 special character."

        return errors

    def validate_login_user(self, user_data):
        errors = {}

        return errors

class User(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username
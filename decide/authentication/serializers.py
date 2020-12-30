from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from django.contrib.auth.models import User
from authentication.models import EmailOTPCode


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_staff')
        validators = [
            UniqueTogetherValidator(queryset=User.objects.all(), fields=['email'])
        ]

class EmailOTPCodeSerializer(serializers.HyperlinkedModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = EmailOTPCode
        fields = ('email', 'callback')
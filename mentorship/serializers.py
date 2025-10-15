from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Dupla, MenteeProfile, MentorProfile, Program, Session, User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class MentorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MentorProfile
        fields = ['user', 'profession', 'experience_years', 'availability', 'interview_notes']


class MenteeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MenteeProfile
        fields = ['user', 'business_name', 'industry', 'challenge_summary', 'interview_notes']


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_('Email'))
    password = serializers.CharField(label=_('Password'), style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class ProgramSerializer(serializers.ModelSerializer):
    mentors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    mentees = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Program
        fields = ['id', 'name', 'client', 'start_date', 'end_date', 'description', 'mentors', 'mentees']


class ProgramAssignmentSerializer(serializers.Serializer):
    mentor_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    mentee_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class DuplaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dupla
        fields = ['id', 'program', 'mentor', 'mentee', 'status', 'start_date', 'end_date']
        read_only_fields = ['id']

    def validate(self, attrs):
        mentor = attrs.get('mentor') or getattr(self.instance, 'mentor', None)
        mentee = attrs.get('mentee') or getattr(self.instance, 'mentee', None)
        program = attrs.get('program') or getattr(self.instance, 'program', None)

        if mentor and mentor.role != User.Role.MENTOR:
            raise serializers.ValidationError({'mentor': 'Selected user is not registered as a mentor.'})
        if mentee and mentee.role != User.Role.MENTEE:
            raise serializers.ValidationError({'mentee': 'Selected user is not registered as a mentee.'})
        if program:
            if mentor and mentor not in program.mentors.all():
                raise serializers.ValidationError({'mentor': 'Mentor is not assigned to this program.'})
            if mentee and mentee not in program.mentees.all():
                raise serializers.ValidationError({'mentee': 'Mentee is not assigned to this program.'})
        return attrs


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            'id',
            'dupla',
            'date',
            'notes_by_mentor',
            'notes_by_mentee',
            'attachments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_dupla(self, value):
        user = self.context['request'].user
        if user.role == User.Role.MENTOR and value.mentor != user:
            raise serializers.ValidationError('Mentors can only create sessions for their own duplas.')
        if user.role == User.Role.MENTEE and value.mentee != user:
            raise serializers.ValidationError('Mentees can only create sessions for their own duplas.')
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.role == User.Role.MENTEE:
            rep.pop('notes_by_mentor', None)
        if request and request.user.role == User.Role.MENTOR:
            rep.pop('notes_by_mentee', None)
        return rep

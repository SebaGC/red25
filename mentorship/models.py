from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        MENTOR = 'mentor', 'Mentor'
        MENTEE = 'mentee', 'Mentee'
        ADMIN = 'admin', 'Administrator'

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class MentorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    profession = models.CharField(max_length=255, blank=True)
    experience_years = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(80)])
    availability = models.JSONField(blank=True, default=dict)
    interview_notes = models.TextField(blank=True)

    def __str__(self):
        return f"MentorProfile<{self.user.email}>"


class MenteeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentee_profile')
    business_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    challenge_summary = models.TextField(blank=True)
    interview_notes = models.TextField(blank=True)

    def __str__(self):
        return f"MenteeProfile<{self.user.email}>"


class Program(models.Model):
    name = models.CharField(max_length=255)
    client = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    mentors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='programs_as_mentor', blank=True)
    mentees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='programs_as_mentee', blank=True)

    def __str__(self):
        return self.name


class Dupla(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        PAUSED = 'paused', 'Paused'

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='duplas')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_duplas')
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentee_duplas')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('program', 'mentor', 'mentee')

    def __str__(self):
        return f"Dupla<{self.program_id}:{self.mentor_id}-{self.mentee_id}>"


def attachment_upload_path(instance, filename):
    return f"sessions/{instance.dupla_id}/{filename}"


class Session(models.Model):
    dupla = models.ForeignKey(Dupla, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    notes_by_mentor = models.TextField(blank=True)
    notes_by_mentee = models.TextField(blank=True)
    attachments = models.FileField(upload_to=attachment_upload_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Session<{self.dupla_id} on {self.date}>"

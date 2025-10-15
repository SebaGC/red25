from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MenteeProfile, MentorProfile, User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role == User.Role.MENTOR:
        MentorProfile.objects.create(user=instance)
    elif instance.role == User.Role.MENTEE:
        MenteeProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_role_profile(sender, instance, **kwargs):
    if instance.role == User.Role.MENTOR and hasattr(instance, 'mentor_profile'):
        instance.mentor_profile.save()
    elif instance.role == User.Role.MENTEE and hasattr(instance, 'mentee_profile'):
        instance.mentee_profile.save()

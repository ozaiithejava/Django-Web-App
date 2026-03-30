import datetime

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class Badge(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default="⭐")
    color = models.CharField(max_length=20, default="#94a3b8")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserProfile(models.Model):
    THEME_CHOICES = [
        ('beyaz', 'Beyaz Tema'),
        ('siyah', 'Siyah Tema'),
        ('mor', 'Mor Tema'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='beyaz')
    manual_badges = models.ManyToManyField(Badge, blank=True, related_name='profiles')
    
    def get_badges(self):
        badges = []
        # 1. AUTO-BADGES
        badges.append({'name': 'Yeni Üye', 'desc': 'Kayıt olan herkese verilir.', 'color': '#94a3b8', 'icon': '🌱'})
        
        now = timezone.now()
        days_active = (now - self.user.date_joined).days
        if days_active >= 30:
            badges.append({'name': 'Kıdemli Üye', 'desc': '30 günden uzun süredir aramızda.', 'color': '#fbbf24', 'icon': '🎖️'})
            
        vote_count = self.user.vote_set.count()
        if vote_count >= 1:
            badges.append({'name': 'İlk Adım', 'desc': 'İlk oyunu kullandı.', 'color': '#60a5fa', 'icon': '🏁'})
        if vote_count >= 5:
            badges.append({'name': 'Aktif Seçmen', 'desc': 'En az 5 ankete oy verdi.', 'color': '#4ade80', 'icon': '⚡'})
        if vote_count >= 20:
            badges.append({'name': 'Anket Canavarı', 'desc': '20 veya daha fazla ankete oy verdi.', 'color': '#c084fc', 'icon': '👾'})
            
        # 2. MANUAL-BADGES
        for mb in self.manual_badges.all():
            badges.append({
                'name': mb.name,
                'desc': mb.description,
                'color': mb.color,
                'icon': mb.icon
            })
            
        return badges

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} voted on {self.question.question_text}"

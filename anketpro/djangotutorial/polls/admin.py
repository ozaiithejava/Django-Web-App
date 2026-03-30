import json
from django.contrib import admin
from django.db.models import Count, Sum
from .models import Choice, Question, UserProfile, Vote, Badge


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "color", "description")
    search_fields = ("name",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "choice", "created_at")
    list_filter = ("created_at", "question")
    search_fields = ("user__username", "question__question_text", "choice__choice_text")
    date_hierarchy = "created_at"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "vote_count")
    list_filter = ("theme",)
    search_fields = ("user__username", "bio")
    filter_horizontal = ("manual_badges",)

    def vote_count(self, obj):
        return obj.user.vote_set.count()
    vote_count.short_description = "Toplam Oy"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Zaman Bilgisi", {"fields": ["pub_date"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "total_votes", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]

    def total_votes(self, obj):
        return obj.choice_set.aggregate(Sum("votes"))["votes__sum"] or 0
    total_votes.short_description = "Toplam Oy"

    def changelist_view(self, request, extra_context=None):
        # Top 5 most voted polls for the chart
        top_questions = Question.objects.annotate(
            total_v=Sum('choice__votes')
        ).order_by('-total_v')[:5]

        chart_data = [
            {
                "label": q.question_text[:30] + "..." if len(q.question_text) > 30 else q.question_text,
                "data": q.total_v or 0
            } for q in top_questions
        ]
        
        # Total stats for the dashboard
        total_polls = Question.objects.count()
        total_votes = Choice.objects.aggregate(Sum('votes'))['votes__sum'] or 0
        total_users = UserProfile.objects.count()

        extra_context = extra_context or {}
        extra_context["chart_data"] = json.dumps(chart_data)
        extra_context["dashboard_stats"] = {
            "total_polls": total_polls,
            "total_votes": total_votes,
            "total_users": total_users,
        }
        return super().changelist_view(request, extra_context=extra_context)

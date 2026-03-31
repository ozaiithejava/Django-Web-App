from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Choice, Question, UserProfile, Vote


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future or those already voted on by the user).
        """
        queryset = Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")
        
        if self.request.user.is_authenticated:
            # Exclude questions the user has already voted on
            voted_question_ids = Vote.objects.filter(user=self.request.user).values_list('question_id', flat=True)
            queryset = queryset.exclude(id__in=voted_question_ids)
            
        return queryset[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


class ChangelogView(generic.TemplateView):
    template_name = "polls/changelog.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    
    if not request.user.is_authenticated:
        return render(request, "polls/detail.html", {
            "question": question,
            "error_message": "Oy vermek için giriş yapmalısınız.",
        })
        
    if Vote.objects.filter(user=request.user, question=question).exists():
        return render(request, "polls/detail.html", {
            "question": question,
            "error_message": "Bu ankette zaten oy kullandınız.",
        })

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        Vote.objects.create(user=request.user, question=question, choice=selected_choice)
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return HttpResponseRedirect(reverse('polls:index'))
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    # Get all votes by this user to display answered polls
    user_votes = Vote.objects.filter(user=profile_user).select_related('question', 'choice').order_by('-created_at')
    
    context = {
        'profile_user': profile_user,
        'user_votes': user_votes,
    }
    return render(request, 'polls/profile.html', context)


@login_required
def edit_profile(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        profile = UserProfile.objects.create(user=request.user)
        
    if request.method == 'POST':
        bio = request.POST.get('bio')
        theme = request.POST.get('theme')
        
        if bio is not None:
            profile.bio = bio
        
        if theme in ['beyaz', 'siyah', 'mor']:
            profile.theme = theme
            
        profile.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('json'):
            from django.http import JsonResponse
            return JsonResponse({'status': 'success'})
            
        return HttpResponseRedirect(reverse('polls:profile', args=(request.user.username,)))
    return render(request, 'polls/profile_edit.html')

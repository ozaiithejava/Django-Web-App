from django import template

register = template.Library()


@register.filter
def vote_percent(votes, question):
    total = sum(c.votes for c in question.choice_set.all())
    if total == 0:
        return 0
    return round((votes / total) * 100)

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
import datetime

# Create your models here.
class Project(models.Model):
    user = models.ForeignKey(User, related_name='project', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateField()
    status = models.CharField(max_length=200, blank=True)
    time_spent = models.DurationField(default=datetime.timedelta(0))

    def __str__(self):
        return f'{self.user.username} - {self.title} - {self.deadline}'
    def formatted_status(self):
        return self.status.replace('_',' ').capitalize()
class Task(models.Model):
    project = models.ForeignKey(Project, related_name='task', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    deadline = models.DateField()
    status = models.CharField(max_length=200)
    priority = models.CharField(max_length=200, blank=True)
    depends_on = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='dependent_tasks')
    time_spent = models.DurationField(default=datetime.timedelta(0))
    timer_started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.project.user} - {self.title} - {self.project.title}'
    def formatted_task_status(self):
        return self.status.replace('_',' ').capitalize()
    def is_unlocked(self):
        if self.depends_on:
            if self.depends_on.status == 'completed':
                return True
            else:
                return False
        return True
    def start_timer(self):
        if not self.timer_started_at:
            self.timer_started_at = now()
    def stop_timer(self):
        if self.timer_started_at:
            time_diff = now() - self.timer_started_at
            self.time_spent += time_diff
            self.timer_started_at = None
            return time_diff
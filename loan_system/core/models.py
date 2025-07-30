from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

class Loan(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    date_applied = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} - {self.amount} KES ({self.status})"

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_saved = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} KES on {self.date_saved.date()}"

class SavingsTarget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField()  # 1 - 12
    year = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year} target: {self.amount}"

class Loan(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255)
    date_applied = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    approval_date = models.DateTimeField(null=True, blank=True)

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class WelfareContribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_contributed = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.amount} KES on {self.date_contributed.strftime('%B %Y')}"

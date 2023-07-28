from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    photo = models.URLField(blank=True)
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class JKFPost(models.Model):
    tid = models.CharField(max_length=10, primary_key=True)
    zone = models.IntegerField()
    name = models.CharField(max_length=50)
    url = models.URLField(blank=True, max_length=50)
    tag = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    is_found = models.BooleanField(default=False)
    status = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class JKFTag(models.Model):
    zone = models.IntegerField()
    tag = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('zone', 'tag'),)
    
    def __str__(self):
        return self.tag

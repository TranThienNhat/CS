from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Auction_Listing(models.Model):
    title = models.CharField(max_length=64)
    image = models.ImageField(upload_to='images/', blank=True)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ManyToManyField(Category, blank=True)
    created_at = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_listings')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}: {self.title} - {self.description} by {self.user}"
    

class Bid(models.Model):
    price_bid = models.DecimalField(max_digits=10, decimal_places=2)
    listing = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}: {self.listing} - {self.price_bid} - {self.user}"   


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    listing = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}: {self.user} - {self.listing} - {self.content} at {self.created_at}"
    

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}: {self.user} - {self.listing}"
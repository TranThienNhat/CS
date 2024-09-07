from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms
from django.contrib import messages
import re

from .models import User, Auction_Listing,Bid,Watchlist, Comment, Category


class CreatingListingForm(forms.ModelForm):
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'placeholder': 'Enter categories separated by commas'
        })
    )

    class Meta:
        model = Auction_Listing
        fields = ['title', 'image', 'description', 'starting_bid', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Enter the title'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Upload an image'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Enter the description',
                'rows': 4 
            }),
            'starting_bid': forms.NumberInput(attrs={
                'class': 'form-control mb-3',
                'placeholder': 'Enter the starting bid'
            }),
        }

        
class CloseForm(forms.ModelForm):
    class Meta:
        model = Auction_Listing
        fields = ['is_active']
        widgets = {
            'is_active': forms.HiddenInput()
        }


class UserBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["price_bid"]
        widgets = {
            'price_bid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your bid',
                'min': '0',
                'step': '0.01',
                'aria-label': 'Price Bid',
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your comment here'})
        }


def index(request):
    listings_with_bids = {}

    listings = Auction_Listing.objects.all()
    for listing in listings:
        latest_bid = Bid.objects.filter(listing=listing).order_by('-price_bid').first()
        listings_with_bids[listing] = latest_bid

    return render(request, "auctions/index.html", {
        "listings_with_bids": listings_with_bids
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == 'POST':
        form = CreatingListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.save()
            category_field = form.cleaned_data.get("category", "")
            category_list = [cat.strip() for cat in re.split(r'[,;/-]', category_field) if cat.strip()]
            for category in category_list:
                category_obj, created = Category.objects.get_or_create(name=category)
                listing.category.add(category_obj)

            Watchlist.objects.get_or_create(user=request.user, listing=listing)

            return redirect('index')
    else:
        form = CreatingListingForm()
    
    return render(request, "auctions/create_listing.html", {'form': form})


def listing(request, listing_id):
    listing = get_object_or_404(Auction_Listing, id=listing_id)
    latest_bid = Bid.objects.filter(listing=listing).order_by('-price_bid').first()
    listings_with_bids = {listing: latest_bid}
    is_in_watchlist = False
    all_comments = Comment.objects.filter(listing=listing)

    if request.user.is_authenticated:
        is_in_watchlist = request.user.watchlist_set.filter(listing=listing).exists() and request.user != listing.user


    if request.method == 'POST':
        if request.user.is_authenticated:
            if listing.is_active:
                if 'close_auction' in request.POST:
                    listing.is_active = False
                    listing.winner_id = latest_bid.user
                    listing.save()
                    Watchlist.objects.filter(user=listing.user, listing=listing).delete()
                    return redirect('index')
                else:
                    form = UserBidForm(request.POST, request.FILES)
                    if form.is_valid():
                        bid = form.save(commit=False)
                        bid.user = request.user
                        bid.listing = listing
                        bid.save()
                        messages.success(request, "Participated in auction")
                        return redirect('listing', listing_id=listing_id)
    else:
        if listing.is_active:
            commentform = CommentForm()
            if request.user.is_authenticated:
                if request.user == listing.user:
                    close_form = CloseForm()
                    form = None
                else:
                    form = UserBidForm()
                    close_form = None
            else:
                form = None
                close_form = None
        else:
            form = None
            close_form = None
            commentform = None

    if not request.user.is_authenticated:
        messages.error(request, "Please login/register an account to participate in the auction.")

    return render(request, "auctions/listing.html", {
        "form": form,
        "close_form": close_form,
        'is_in_watchlist': is_in_watchlist,
        "listings_with_bids": listings_with_bids,
        "commentform": commentform,
        "all_comments": all_comments
    })


def watchlist(request, listing_id):
    listing = Auction_Listing.objects.get(id=listing_id)
    user = request.user
    if user == listing.user:
        messages.error(request, "You cannot remove your own listing from your watchlist.")
    else:
        watchlist_item, created = Watchlist.objects.get_or_create(user=user, listing=listing)
        if not created:
            watchlist_item.delete()

    return redirect('listing', listing_id=listing_id)



def comment(request,listing_id):
    listing = get_object_or_404(Auction_Listing, id=listing_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.listing = listing
            comment.save()
            messages.success(request, "Comments have been added")
            return redirect('listing', listing_id=listing_id)


def watchlisting(request):
    if request.user.is_authenticated:
        user = request.user.id
        listings = Watchlist.objects.filter(user=user)
        return render(request, "auctions/watchlisting.html", {
            "listings": listings
        })


def categories(request):
    categories = Category.objects.all().distinct()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category_listings(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    listings = Auction_Listing.objects.filter(category=category, is_active=True)
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })
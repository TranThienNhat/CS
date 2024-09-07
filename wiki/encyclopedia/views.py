from django.shortcuts import render, redirect
import markdown2
import random

from . import util


def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

def entry(request, title):
    entrypage = util.get_entry(title)
    if entrypage is not None:
        html_content = markdown2.markdown(entrypage)
        return render(request, "encyclopedia/entry.html", {
            "entry": html_content,
            "title": title
        })
    else:
        return render(request, "encyclopedia/error.html", {
            "title": title
        })
    

def search(request):
    if request.method == 'POST':
        query = request.POST.get('q', '').strip()
        search_entry = util.get_entry(query)
        if search_entry is not None:
                html_content = markdown2.markdown(search_entry)
                return render(request, "encyclopedia/search.html", {
                    "entry": html_content,
                    "title": query
                })
        else:
            all_entries = util.list_entries()
            matching_entries = [entry for entry in all_entries if query.lower() in entry.lower()]
            return render(request, "encyclopedia/search_results.html", {
                "entries": matching_entries,
                "title": query
            })
        

def create(request):
     if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        title_create = util.get_entry(title)

        if title_create is not None:
            if title_create is not None:
                return render(request, "encyclopedia/create.html", {
                    "error": "An entry with this title already exists."
                }) 
        else:
             util.save_entry(title, request.POST.get('content', '').strip())
             return redirect('entry', title=title)
     else:
          return render(request, "encyclopedia/create.html")


def save_edit(request, title):
    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()
        util.save_entry(title, new_content)
        return redirect('entry', title=title)
    else:
        content = util.get_entry(title)
        if content is None:
            return render(request, "encyclopedia/error.html", {
                "message": "Entry not found."
            })
        return render(request, "encyclopedia/edit.html", {
            "title": title,
            "content": content
        })
    

def random_page(request):
    entries = util.list_entries()
    if entries:
        random_entry = random.choice(entries)
        return redirect('entry', title=random_entry)
    return redirect('index')
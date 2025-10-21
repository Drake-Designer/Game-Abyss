from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import BlogPostForm


def new_post(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Puoi cambiare la redirect alla lista post
            return redirect('blog:new')
    else:
        form = BlogPostForm()
    return render(request, 'blog/new_post.html', {'form': form})

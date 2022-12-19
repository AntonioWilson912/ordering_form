from django.shortcuts import render, redirect

# Create your views here.
def dashboard(request):
    # if not "user_id" in request.session:
    #     return redirect("/")
    return render(request, "view_companies.html")
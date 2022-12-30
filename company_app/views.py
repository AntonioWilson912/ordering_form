from django.shortcuts import render, redirect
from .models import Company
from user_app.models import User

# Create your views here.
def dashboard(request):
    # if not "user_id" in request.session:
    #     return redirect("/")
    context = {
        #"logged_in_user": User.objects.get(id=request.session["user_id"]),
        "all_companies": Company.objects.all()
    }
    return render(request, "view_companies.html", context)
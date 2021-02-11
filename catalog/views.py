from django.shortcuts import render
from django.urls.base import reverse_lazy

# Create your views here.
from catalog.models import Book, Author, BookInstance, Genre

def index(request):
  """View function for home page of site."""

  # Generate counts of some of the main objects
  num_books = Book.objects.all().count()
  num_instances = BookInstance.objects.all().count()

  # Available books (status = 'a')
  num_instances_available = BookInstance.objects.filter(status__exact='a').count()

  # The 'all()' is implied by default.
  num_authors = Author.objects.count()

  # How many genres are already present
  num_genres = Genre.objects.count()

  # Books containing an "and" -> case-insensitive
  num_books_with_and = Book.objects.filter(title__icontains='and').count()

   # Genres containing an "f" -> case-insensitive
  num_genres_with_f = Genre.objects.filter(name__icontains='f').count()

  # Number of visits to this view, as counted in the session variable.
  num_visits = request.session.get('num_visits', 1)
  request.session['num_visits'] = num_visits + 1

  context = {
    'num_books': num_books,
    'num_instances':num_instances,
    'num_instances_available':num_instances_available,
    'num_authors':num_authors,
    'num_genres':num_genres,
    'num_books_with_and':num_books_with_and,
    'num_genres_with_f':num_genres_with_f,
    'num_visits': num_visits,
  }

  # Render the HTML template index.html with the data in the context variable
  return render(request,'index.html',context=context)


## Generic list views..
from django.views import generic

class BookListView(generic.ListView):
  model = Book
  paginate_by = 10

class BookDetailView(generic.DetailView):
  model = Book

class AuthorListView(generic.ListView):
  model = Author
  paginate_by = 10

class AuthorDetailView(generic.DetailView):
  model = Author

## Author Archive List View...
class AuthorBirthYearListView(generic.ListView):
  model = Author
  template_name = 'catalog/author_birth_year_list.html'

  def get_queryset(self):
    return Author.objects.filter(date_of_birth__year=self.kwargs['year'])

  def get_context_data(self, **kwargs):
    # Call the base implementation first to get the context
    context = super(AuthorBirthYearListView, self).get_context_data(**kwargs)
    # Create any data and add it to the context
    context['birth_year'] = self.kwargs['year']
    return context

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

class LoanedBooksByUserListView(LoginRequiredMixin,UserPassesTestMixin,generic.ListView):
  """Generic class-based view listing books on loan to current user.""" 
  model = BookInstance
  template_name ='catalog/bookinstance_list_borrowed_user.html'
  paginate_by = 10

  def test_func(self):
      return self.request.user.groups.filter(name='Library Members').exists()

  def get_queryset(self):
      return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

from django.urls import reverse

class LoanedBooksByLibrarianListView(PermissionRequiredMixin, generic.ListView):
  permission_required = 'catalog.can_mark_returned'

  """Generic class-based view listing books on loan to current user."""
  model = BookInstance
  template_name ='catalog/bookinstance_list_borrowed.html'
  paginate_by = 10

  def get_queryset(self):
      return BookInstance.objects.filter(status__exact='o').order_by('due_back')

import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookModelForm

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request,pk):
  book_instance = get_object_or_404(BookInstance,pk=pk)

  # If this is a POST request then process the Form data
  if request.method == 'POST':

    # Create a form instance and populate it with data from the request (binding):
    form = RenewBookModelForm(request.POST)

    # Check if the form is valid:
    if form.is_valid():
        # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
        book_instance.due_back = form.cleaned_data['due_back']
        book_instance.save()

        # redirect to a new URL:
        return HttpResponseRedirect(reverse('borrowed') )

  # If this is a GET (or any other method) create the default form.
  else:
    proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
    form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})

  context = {
      'form': form,
      'book_instance': book_instance,
  }

  return render(request, 'catalog/book_renew_librarian.html', context)

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author, Book

class AuthorCreate(PermissionRequiredMixin, CreateView):

  permission_required = 'catalog.can_modify_author_list'

  model = Author
  fields = ['first_name','last_name','date_of_birth','date_of_death']
  initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView):

  permission_required = 'catalog.can_modify_author_list'

  model = Author
  fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(PermissionRequiredMixin, DeleteView):

  permission_required = 'catalog.can_modify_author_list'
  model = Author
  success_url = reverse_lazy('authors')

### BOOK DATA MODIFICATION VIEWS ###
class BookCreate(PermissionRequiredMixin, CreateView):

  permission_required = 'catalog.add_book'

  model = Book
  fields = ['title','author','language','summary','isbn','genre']

class BookUpdate(PermissionRequiredMixin, UpdateView):

  permission_required = 'catalog.change_book'

  model = Book
  fields = ['title','author','language','summary','isbn','genre']

class BookDelete(PermissionRequiredMixin, DeleteView):

  permission_required = 'catalog.delete_book'

  model = Book
  success_url = reverse_lazy('authors')

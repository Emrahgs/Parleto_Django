from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .forms import CategoryCreateForm, ExpenseSearchForm
from .models import Expense, Category
from .reports import summary_per_category, summary_per_year_month
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum



class ExpenseListView(ListView):
    model = Expense

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        paginator = Paginator(queryset, 3)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        try:
            paginated = paginator.get_page(page_number)
        except PageNotAnInteger:
            paginated = paginator.get_page(1)
        except EmptyPage:
            paginated = paginator.page(paginator.num_pages)

        form = ExpenseSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            if name:
                queryset = queryset.filter(name__icontains=name)

            category = form.cleaned_data['category']
            if category:
                queryset = queryset.filter(category=category)

            grouping = form.cleaned_data['grouping']
            if grouping:
                queryset = queryset.order_by('date', '-pk')

        return super().get_context_data(
            form=form,
            object_list=page_obj,
            DataPaginated=paginated,
            summary_per_category=summary_per_category(queryset),
            summary_per_year_month=summary_per_year_month(queryset),
            **kwargs)


class CategoryCreateView(CreateView):
    model = Category
    fields = ('name',)
    success_url=reverse_lazy('expenses:expense-list')

    def get(self, request, *args, **kwargs):
        context = {'form': CategoryCreateForm()}
        return render(request, 'expenses/category-create.html', context)

    def post(self, request, *args, **kwargs):
        form = CategoryCreateForm(request.POST)
        if form.is_valid():
            category = form.save()
            category.save()
            return redirect(self.success_url)
        return render(request, 'expenses/category-create.html', {'form': form})

    def validate_name(name):
        names = Category.objects.values_list('name', flat=True)
        print(names, 'names')
        if name in names:
            raise ValidationError("Already exists this category")


class CategoryUpdateView(UpdateView):
    model = Category
    template_name = 'expenses/category-update.html'
    fields = ('name',)
    success_url ='/expenses/category/list'

    def validate_name(name):
        names = Category.objects.values_list('name', flat=True)
        if name in names:
            raise ValidationError("Already exists this category")


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'expenses/category-delete.html'
    success_url ='/expenses/category/create'


class CategoryListView(ListView):
    model = Category
    template_name = 'expenses/category-list.html'
    context_object_name = 'categories'
    
    def get(self, request):
        paginate_by = request.GET.get('paginate_by', 1) or 1
        data = Category.objects.all()
        paginator = Paginator(data, paginate_by)
        page = request.GET.get('page')

        try:
            paginated = paginator.get_page(page)
        except PageNotAnInteger:
            paginated = paginator.get_page(1)
        except EmptyPage:
            paginated = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'DataPaginated':paginated, 'paginate_by':paginate_by})

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'expenses/bycategory-list.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Expense.objects.filter(category__id=self.kwargs.get('pk'))
        total = Expense.objects.filter(category__id=self.kwargs.get('pk')).aggregate(Sum('amount')).get('amount__sum')
        if total == None:
            total = 0
        context['expenses'] = queryset
        context['all'] = Expense.objects.all()
        context['total'] = total
        return context
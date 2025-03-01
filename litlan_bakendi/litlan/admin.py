from django.contrib import admin
from .models import Crossword, Cell, Hint

class CellInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = Cell
    extra = 0  # Number of empty forms to display
    fields = ('x_coord', 'y_coord', 'value', 'is_blank')
    ordering = ('y_coord', 'x_coord')

class HintInline(admin.TabularInline):
    model = Hint
    extra = 0
    fields = ('x_coord', 'y_coord', 'direction', 'text')
    ordering = ('y_coord', 'x_coord')

class CrosswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'width', 'height')
    search_fields = ('date',)
    inlines = [CellInline, HintInline]

admin.site.register(Crossword, CrosswordAdmin)

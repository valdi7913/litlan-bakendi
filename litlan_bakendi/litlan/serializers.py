from rest_framework import serializers
from .models import Crossword, Cell, Hint, Word

class CellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell
        fields = ['value', 'is_blank', 'x_coord', 'y_coord']

class HintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hint
        fields = ['id', 'x_coord', 'y_coord', 'direction', 'text']

class CrosswordSerializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()
    hints = serializers.SerializerMethodField()
    
    class Meta:
        model = Crossword
        fields = ['id', 'date', 'width', 'height', 'cells', 'hints']
    
    def get_cells(self, obj):
        cells = Cell.objects.filter(crossword=obj)
        return CellSerializer(cells, many=True).data
    
    def get_hints(self, obj):
        hints = Hint.objects.filter(crossword=obj)
        return HintSerializer(hints, many=True).data

class ValidationRequestSerializer(serializers.Serializer):
    puzzle_id = serializers.IntegerField()
    answers = serializers.DictField(child=serializers.CharField())
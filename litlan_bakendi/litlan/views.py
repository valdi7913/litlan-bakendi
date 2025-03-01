from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Crossword, Cell, Hint
from .serializers import CrosswordSerializer, ValidationRequestSerializer

class DailyPuzzleView(APIView):
    def get(self, request):
        # Get today's date
        today = timezone.now().date()
        
        try:
            # Get today's crossword puzzle
            puzzle = Crossword.objects.get(date=today)
            serializer = CrosswordSerializer(puzzle)
            return Response(serializer.data)
        except Crossword.DoesNotExist:
            # Handle case where there's no puzzle for today
            return Response(
                {"error": "No puzzle available for today."},
                status=status.HTTP_404_NOT_FOUND
            )

class ValidateAnswersView(APIView):
    def post(self, request):
        serializer = ValidationRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            puzzle_id = serializer.validated_data['puzzle_id']
            user_answers = serializer.validated_data['answers']
            
            try:
                puzzle = Crossword.objects.get(id=puzzle_id)
                
                # Get all hints for this puzzle
                hints = Hint.objects.filter(crossword=puzzle)
                
                # Build a dictionary of expected answers
                expected_answers = {}
                for hint in hints:
                    # Get all cells for this hint in the correct direction
                    answer = ""
                    if hint.direction == 'Horizontal':
                        cells = Cell.objects.filter(
                            crossword=puzzle,
                            y_coord=hint.y_coord,
                            x_coord__gte=hint.x_coord,
                            is_blank=False
                        ).order_by('x_coord')
                        for cell in cells:
                            answer += cell.value
                            # Stop if we reach a blank cell or the edge
                            if Cell.objects.filter(
                                crossword=puzzle,
                                y_coord=hint.y_coord,
                                x_coord=cell.x_coord+1,
                                is_blank=True
                            ).exists() or cell.x_coord == puzzle.width - 1:
                                break
                    else:  # Vertical
                        cells = Cell.objects.filter(
                            crossword=puzzle,
                            x_coord=hint.x_coord,
                            y_coord__gte=hint.y_coord,
                            is_blank=False
                        ).order_by('y_coord')
                        for cell in cells:
                            answer += cell.value
                            # Stop if we reach a blank cell or the edge
                            if Cell.objects.filter(
                                crossword=puzzle,
                                x_coord=hint.x_coord,
                                y_coord=cell.y_coord+1,
                                is_blank=True
                            ).exists() or cell.y_coord == puzzle.height - 1:
                                break
                    
                    expected_answers[str(hint.id)] = answer
                
                # Validate user answers
                results = {}
                for hint_id, answer in user_answers.items():
                    if hint_id in expected_answers:
                        results[hint_id] = answer.upper() == expected_answers[hint_id].upper()
                    else:
                        results[hint_id] = False
                
                # Calculate overall correctness
                total = len(results)
                correct = sum(1 for val in results.values() if val)
                percentage = (correct / total * 100) if total > 0 else 0
                
                return Response({
                    "results": results,
                    "correct": correct,
                    "total": total,
                    "percentage": percentage
                })
                
            except Crossword.DoesNotExist:
                return Response(
                    {"error": "Puzzle not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
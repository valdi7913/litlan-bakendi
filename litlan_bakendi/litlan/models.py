from django.db import models

class DirectionChoices(models.TextChoices):
    VERTICAL = 'Vertical', 'Vertical'
    HORIZONTAL = 'Horizontal', 'Horizontal'

class Crossword(models.Model):
    # id field is automatically created as SERIAL PRIMARY KEY
    date = models.DateField()
    width = models.IntegerField()
    height = models.IntegerField()
    
    class Meta:
        db_table = 'crossword'

class Cell(models.Model):
    crossword = models.ForeignKey(Crossword, on_delete=models.CASCADE, db_column='crossword_id')
    value = models.CharField(max_length=1)
    is_blank = models.BooleanField()
    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    
    class Meta:
        db_table = 'cell'
        # Define composite primary key
        unique_together = (('crossword', 'x_coord', 'y_coord'),)
        # Note: Django doesn't support true composite primary keys, 
        # so we use unique_together constraint instead

class Hint(models.Model):
    crossword = models.ForeignKey(Crossword, on_delete=models.CASCADE, db_column='crossword_id')
    id = models.AutoField(primary_key=True)
    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    direction = models.CharField(
        max_length=10,
        choices=DirectionChoices.choices
    )
    text = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'hint'
        unique_together = (('crossword', 'x_coord', 'y_coord', 'direction'),)
        # Note: Django will actually use an auto-generated id field as the real primary key,
        # but we need to maintain the composite primary key for database compatibility

class Word(models.Model):
    # id field is automatically created as SERIAL PRIMARY KEY
    text = models.TextField()
    definition = models.TextField()
    
    class Meta:
        db_table = 'word'
# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, URLField
from wtforms.validators import DataRequired, Optional, URL, Email

class AddTaskForm(FlaskForm):
    service = SelectField('Выберите Услугу или Пакет', choices=[], validators=[DataRequired()])
    submit = SubmitField('Добавить Задачу')

class AddPropertyForm(FlaskForm):
    status = SelectField('Статус', choices=[
        ("Ожидание ответа агента", "Ожидание ответа агента"),
        ("Бронь забронирована", "Бронь забронирована"),
        ("Иду смотреть", "Иду смотреть"),
        ("Идет просмотр объекта", "Идет просмотр объекта"),
        ("Объект просмотрен", "Объект просмотрен"),
        ("Результат готов", "Результат готов"),
        ("Просмотр отменен", "Просмотр отменен"),
    ], validators=[DataRequired()])
    
    link = URLField('Ссылка на Объект', validators=[Optional(), URL(message="Введите корректный URL.")])
    
    additional_info = StringField('Дополнительная Информация', validators=[Optional()])
    
    submit = SubmitField('Добавить Недвижимость')

class UpdateUserInfoForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    language = SelectField('Язык', choices=[
        ('ru', 'Русский'),
        ('en', 'English'),
        ('uz', 'O‘zbekcha')
    ], validators=[DataRequired()])
    submit = SubmitField('Обновить')
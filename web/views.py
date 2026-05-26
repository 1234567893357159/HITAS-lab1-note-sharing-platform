from flask import Blueprint, render_template, request, redirect, url_for
from .models import Note, Comment
from .producer.producer import MessageProducer

views = Blueprint('views', __name__)
middleware_host = 'localhost'  # Update with your middleware host
middleware_port = 5000  # Update with your middleware port
producer = MessageProducer(middleware_host, middleware_port)

@views.route('/')
def index():
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@views.route('/note/<int:note_id>', methods=['GET', 'POST'])
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    if request.method == 'POST':
        comment_content = request.form['comment']
        new_comment = Comment(content=comment_content, note_id=note.id)
        new_comment.save()
        
        # Send comment event to middleware
        message_content = {
            'note_id': note.id,
            'user_id': 1,  # Replace with actual user ID
            'content': comment_content
        }
        producer.send_message('note/comment', message_content)
        
        return redirect(url_for('views.note_detail', note_id=note.id))
    
    comments = note.comments
    return render_template('note_detail.html', note=note, comments=comments)

@views.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_note = Note(title=title, content=content)
        new_note.save()
        
        # Send publish event to middleware
        message_content = {
            'note_id': new_note.id,
            'user_id': 1,  # Replace with actual user ID
            'content': content
        }
        producer.send_message('note/publish', message_content)
        
        return redirect(url_for('views.index'))
    
    return render_template('add_note.html')
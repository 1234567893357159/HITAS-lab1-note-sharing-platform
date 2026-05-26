// This file contains JavaScript code for handling client-side interactions.

document.addEventListener('DOMContentLoaded', function() {
    // Function to load notes and display them on the main page
    function loadNotes() {
        fetch('/api/notes')
            .then(response => response.json())
            .then(data => {
                const notesContainer = document.getElementById('notes-container');
                notesContainer.innerHTML = '';
                data.notes.forEach(note => {
                    const noteElement = document.createElement('div');
                    noteElement.className = 'note';
                    noteElement.innerHTML = `
                        <h3>${note.title}</h3>
                        <p>${note.summary}</p>
                        <a href="/note/${note.id}">查看详情</a>
                    `;
                    notesContainer.appendChild(noteElement);
                });
            });
    }

    // Function to handle adding a new note
    document.getElementById('add-note-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/api/notes', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadNotes();
                alert('笔记添加成功！');
                this.reset();
            } else {
                alert('添加笔记失败：' + data.message);
            }
        });
    });

    // Function to handle liking a note
    window.likeNote = function(noteId) {
        fetch(`/api/notes/${noteId}/like`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('点赞成功！');
                // Optionally, update the like count on the page
            } else {
                alert('点赞失败：' + data.message);
            }
        });
    };

    // Load notes when the page is ready
    loadNotes();
});
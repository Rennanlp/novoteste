from flask import Flask, render_template, request, redirect, url_for

tasks = []

def task():
    return render_template('index.html', tasks=tasks)

def add_task():
    new_task = request.form.get('task')
    tasks.append(new_task)
    return redirect(url_for('index'))